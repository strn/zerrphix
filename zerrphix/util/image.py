from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import os
import tempfile

from PIL import Image, ImageFont

import zerrphix.template
from zerrphix.util.filesystem import get_file_extension
from zerrphix.util.text import split_into_sentences
from zerrphix.util.web import download

log = logging.getLogger(__name__)


# http://web.archive.org/web/20130115175340/http://nadiana.com/pil-tutorial-basic-advanced-drawing

def text_line_calc_font_size(draw, text, font_path, font_type, font_min_size, font_max_size, width,
                             height):
    log.debug('text %s, font_min_size %s, font_max_size %s, width %s, height %s',
              text, font_min_size, font_max_size, width, height)
    for font_size in reversed(range(font_min_size, font_max_size+1)):
        if font_type == 'truetype':
            font = ImageFont.truetype(font_path, font_size)
        draw_text_size = draw.textsize(text, font)
        log.debug('font_size %s, width %s, height %s', font_size, draw_text_size[0], draw_text_size[1])
        if draw_text_size[0] <= width and draw_text_size[1] <= height:
            log.debug('%s <= %s and %s <= height %s', draw_text_size[0], width, draw_text_size[1], height)
            return font_size
        else:
            log.debug('NOT %s <= %s and %s <= height %s', draw_text_size[0], width, draw_text_size[1], height)
    return font_min_size

def text_line(draw, x, y, text, font_path, font_type, font_min_size, font_max_size,
              colour, halign, valign, width, height, use_dotdotdot=False):
    """
    Deafult align is top left (halign = left and valign = top)
    """
    # print(locals())
    input_text = text
    dotdotdot = False
    if isinstance(width, int):
        if font_max_size < font_min_size:
            log.debug('font_max_size %s < font_min_size %s', font_max_size, font_min_size)
            font_max_size = font_min_size
        if font_max_size == font_min_size:
            log.debug('font_max_size %s == font_min_size %s or height %s is None',
                      font_max_size, font_min_size, height)
            font_size = font_min_size
        else:
            log.debug('text_line_calc_font_size')
            font_size = text_line_calc_font_size(
                draw, text, font_path, font_type, font_min_size, font_max_size, width, height
            )
        if font_type == 'truetype':
            font = ImageFont.truetype(font_path, font_size)
        while text:
            draw_text_size = draw.textsize(text, font)
            if draw_text_size[0] <= width:
                # print(text)
                if dotdotdot:
                    text = '{0}...'.format(text[:-2])
                    # print('text', text)
                    # print('x,y', x,y)
                draw_text_size = draw.textsize(text, font)
                # print('draw_text_size', draw_text_size)
                offset = font.getoffset(text)
                # print('offset', offset)
                draw_text_size_offset = (draw_text_size[0] - offset[0], draw_text_size[1] - offset[1])
                # print('draw_text_size_offset', draw_text_size_offset)
                aligment = align(draw_text_size_offset, halign, valign)
                # print('aligment', aligment)
                draw_position = (x - aligment[0] - offset[0], y - (aligment[1] + offset[1]))
                draw.text(draw_position, text, font=font, fill=colour)
                # print('draw_position', draw_position)
                return
            else:
                if use_dotdotdot:
                    dotdotdot = True
                text = text[:-1].strip()
        log.debug('text: {0} does not fit into width: {1} even with only the first charactor'.format(
            input_text, width))
        return
    else:
        if font_type == 'truetype':
            font = ImageFont.truetype(font_path, font_max_size)
        # print('text', text)
        # print('x,y', x,y)
        draw_text_size = draw.textsize(text, font)
        # print('draw_text_size', draw_text_size)
        offset = font.getoffset(text)
        # print('offset', offset)
        draw_text_size_offset = (draw_text_size[0] - offset[0], draw_text_size[1] - offset[1])
        # print('draw_text_size_offset', draw_text_size_offset)
        aligment = align(draw_text_size_offset, halign, valign)
        # print('aligment', aligment)
        draw_position = (x - aligment[0] - offset[0], y - (aligment[1] + offset[1]))
        draw.text(draw_position, text, font=font, fill=colour)
        # print('draw_position', draw_position)


def align(draw_text_size, halign, valign):
    # print(draw_text_size)
    # print(x, y)
    x = horizontal_align(draw_text_size, halign)
    y = vertical_align(draw_text_size, valign)
    # print(x, y)
    return (x, y)


def horizontal_align(draw_text_size, align):
    # print('horizontal', align)
    if align == 'center' or align == 'centre':
        x = draw_text_size[0] / 2
    elif align == 'right':
        x = draw_text_size[0]
    else:
        return 0
    return x


def vertical_align(draw_text_size, align):
    # print('vertical', align)
    if align == 'middle':
        y = draw_text_size[1] / 2
    elif align == 'bottom':
        y = draw_text_size[1]
    else:
        return 0
    return y


def text_box(draw, text, font_file_path, box_width, box_height, font_min_size,
             font_max_size, x, y, line_spacing, split_char=' ', use_sentences=0):
    # If the font_min_size is grater than font_max_size then that is invalid
    # therefore set font_max_size to font_min_size
    if font_max_size < font_min_size:
        font_max_size = font_min_size
    # if font_max_size is greater than font_main_size
    # generate a list of values from min to max
    if font_max_size > font_min_size:
        font_sizes = range(font_min_size, font_max_size + 1)
    # else set font_sizes to list with font_min_size only
    else:
        font_sizes = [font_min_size]
    # if we are to use sentences
    if use_sentences == 1:
        # put each sentence as string into a list
        sentenses = split_into_sentences(text)
        # first sentence incase the first sentence does not fit in the defined
        # box size
        first_sentance = sentenses[0]
        # while sentences list is not empty
        while sentenses:
            # for each font size reverse (i.e. start with the largest font size)
            for font_size in reversed(font_sizes):
                # setup font
                font = ImageFont.truetype(font_file_path,
                                          font_size)
                # setup line spacing
                current_font_size_line_spacing = int((font_size / 7) + line_spacing)
                # print(line_spacing)
                # print(font_size)
                # try and get lines with current sentences list and font size
                lines = text_box_calc(draw, sentenses, split_char, font, font_size, current_font_size_line_spacing,
                                      box_width, box_height)
                # senteneces and lines with current font size will fit in the defined box
                if lines != False:
                    # return the lines, line spacing and font
                    return lines, line_spacing, font
            # remove the last sentnce in sentences list as there are
            # too many to fit inside the defined box
            sentenses.pop()

        # We were not able to get even the just the first sentece to fit
        # in the defined box so lets just use the first one up until it
        # does not fit in the box anymore

        # set font size to the minimum
        font_size = font_min_size
        # setup font
        font = ImageFont.truetype(font_file_path, font_size)
        # setup line spacing
        line_spacing = (font_size / 100) * line_spacing
        # get lines up until they do not fit the defined box
        lines = text_box_calc(draw, sentenses, split_char, font, font_size, line_spacing, box_width, box_height,
                              return_on_overheight=True)

        if lines != False:
            return lines, line_spacing, font

    # We are not using sentences
    else:
        sentenses = [text]
        # for each font size reverse (i.e. start with the largest font size)
        for font_size in reversed(font_sizes):
            # setup font
            font = ImageFont.truetype(font_file_path,
                                      font_size)
            # setup line spacing
            line_spacing = (font_size / 100) * line_spacing
            # try and get lines with current sentences list and font size and append split char to each item in sentences
            lines = text_box_calc(draw, sentenses, split_char, font, font_size, line_spacing, box_width, box_height,
                                  append_split_char=True)
            if not lines:
                lines = text_box_calc(draw, sentenses, split_char, font, font_min_size, line_spacing, box_width,
                                      box_height, append_split_char=True, return_on_overheight=True)
            if lines != False:
                return lines, line_spacing, font


def text_box_calc(draw, sentenses, split_char, font, font_size, line_spacing, box_width,
                  box_height, start_setance_new_line=False, return_on_overheight=False, append_split_char=False):
    # setup lines
    lines = []
    # setup draw_list
    draw_list = []
    # setup line
    line = ''
    # set current line height to 0
    current_height = 0
    # for each sentence in sentences
    for sentence in sentenses:
        # for each word in sentence split into a list by split char
        for word in sentence.split(split_char):
            # if there is no text in the line we do not want to add
            # add a space at the beggining of the line
            if not line:
                # append split char to line as append_split_char is True
                if append_split_char:
                    new_line_dims = draw.textsize('{0} {1}{2}'.format(line, word, split_char), font)
                    new_line_offset = font.getoffset('{0} {1}{2}'.format(line, word, split_char))
                else:
                    new_line_dims = draw.textsize('{0} {1}'.format(line, word), font)
                    new_line_offset = font.getoffset('{0} {1}'.format(line, word))
                # if word added to line exceeds the allowed width
                if new_line_dims[0] - new_line_offset[0] > box_width:
                    # TODO: as the word exceeds the line width this needs to be dealt with properly
                    log.critical('need to deal with word bigger then the allowed width')
                    #raise SystemExit

                # word added to line does not exceed box_width
                # so lets check if it exceeds box_height
                # if there allready is a line use line_spacing in calculation
                if lines or draw_list:
                    if (new_line_dims[1] - new_line_offset[1] + current_height + line_spacing) > box_height:
                        if return_on_overheight:
                            if start_setance_new_line == True:
                                draw_list.extend(lines)
                                return draw_list
                            else:
                                return lines
                        return False
                # There are not currently any lines so we won't use line spaceing
                # and current lines in calcualtion
                else:
                    if (new_line_dims[1] - new_line_offset[1]) > box_height:
                        if return_on_overheight:
                            if start_setance_new_line == True:
                                draw_list.extend(lines)
                                return draw_list
                            else:
                                return lines
                        return False
                # new line does not exced box_width and box_height
                # so set line to word as line is currently empty
                if append_split_char:
                    line = '{0}{1}'.format(word, split_char)
                else:
                    line = word

            # line is not empty
            else:
                # if we are to append split char to each word
                if append_split_char:
                    new_line_width = draw.textsize('{0} {1}{2}'.format(line, word, split_char), font)[0] - \
                                     font.getoffset('{0} {1}{2}'.format(line, word, split_char))[0]
                else:
                    new_line_width = draw.textsize('{0} {1}'.format(line, word), font)[0] - \
                                     font.getoffset('{0} {1}'.format(line, word))[0]

                # check if we add the current word (and also optionally split char) to the current
                # line that is will not exceed the pre defined maximum width box_width
                if new_line_width > box_width:
                    # adding the current word to the current line will make the current line
                    # too long. Now lets check if the overall height will be too big if we
                    # add a new line containing 'word'
                    line_height = draw.textsize(line, font)[1] - font.getoffset(line)[1]
                    next_line_height = draw.textsize(word, font)[1] - font.getoffset(word)[1]
                    if (current_height + line_height + next_line_height + line_spacing) > box_height:
                        # if we are to return on overheight
                        if return_on_overheight:
                            if append_split_char:
                                line = line.rstrip(split_char)
                            lines.append(line)
                            if start_setance_new_line == True:
                                draw_list.extend(lines)
                                return draw_list
                            else:
                                return lines
                        else:
                            return False
                    # current_height + line_height + next_line_height + line_spacing does not exceed
                    # box_height
                    else:
                        current_height += (line_height + line_spacing)

                    # as word added to line exceeeds box_width
                    # put current line into lines and start a new line
                    lines.append(line)
                    if append_split_char:
                        line = '{0}{1}'.format(word, split_char)
                    else:
                        line = word

                # new line width is not greater than box width so append word to line
                else:
                    if append_split_char:
                        ammended_line_height = draw.textsize('{0}{1}'.format(word, split_char), font)[1] - \
                                               font.getoffset('{0}{1}'.format(word, split_char))[1]
                    else:
                        ammended_line_height = draw.textsize(' {0}'.format(word), font)[1] - \
                                               font.getoffset(' {0}'.format(word))[1]

                    if (ammended_line_height + line_spacing) > box_height:
                        if return_on_overheight:
                            if start_setance_new_line == True:
                                draw_list.extend(lines)
                                if draw_list and append_split_char:
                                    draw_list[-1] = draw_list[-1].rstrip(split_char)
                                return draw_list
                            else:
                                if lines and append_split_char:
                                    lines[-1] = lines[-1].rstrip(split_char)
                                return lines
                        else:
                            return False

                    if append_split_char:
                        line += '{0}{1}'.format(word, split_char)
                    else:
                        line += ' {0}'.format(word)
        # as we have some to the end of the sentence
        # if the current line is not empty, it needs to be added to lines if we are starting each setence on a new line
        if start_setance_new_line == True:
            lines.append(line)
            lines = []
            line = ''
            draw_list.extend(lines)

    if line:
        lines.append(line)
        line = ''

    if start_setance_new_line == True:
        if lines:
            draw_list.extend(lines)
        if draw_list and append_split_char:
            draw_list[-1] = draw_list[-1].rstrip(split_char)
        return draw_list
    else:
        if lines and append_split_char:
            lines[-1] = lines[-1].rstrip(split_char)
        return lines


def paste(background_image_path, foreground_image_path, output_image_path, offset, mask=False):
    foreground_image = Image.open(foreground_image_path)
    background_image = Image.open(background_image_path)

    if mask == True:
        background_image.paste(foreground_image, offset, mask=foreground_image)
    else:
        background_image.paste(foreground_image, offset)

    background_image.save(output_image_path)


def resize_and_crop2(img_path, modified_path, size, crop_type='top'):
    """
    https://gist.github.com/sigilioso/2957026

    Resize and crop an image to fit the specified size.

    args:
    img_path: path for the image to resize.
    modified_path: path to store the modified image.
    crop_type: can be 'top', 'middle' or 'bottom', depending on this
    value, the image will cropped getting the 'top/left', 'middle' or
    'bottom/right' of the image to fit the size.
    raises:
    Exception: if can not open the file in img_path of there are problems
    saving the image.
    ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
                   int(round((img.size[1] + size[1]) / 2)))
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = (int(round((img.size[0] - size[0]) / 2)), 0,
                   int(round((img.size[0] + size[0]) / 2)), img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]),
                         Image.ANTIALIAS)
    # If the scale is the same, we do not need to crop
    img.save(modified_path)


def resize_and_crop(img_path, size, crop_type='top', asptect_ratio_change_threshold=None):
    """
    https://gist.github.com/sigilioso/2957026

    Resize and crop an image to fit the specified size.

    args:
    img_path: path for the image to resize.
    modified_path: path to store the modified image.
    crop_type: can be 'top', 'middle' or 'bottom', depending on this
    value, the image will cropped getting the 'top/left', 'middle' or
    'bottom/right' of the image to fit the size.
    raises:
    Exception: if can not open the file in img_path of there are problems
    saving the image.
    ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    log.debug('ratio %s', ratio)
    log.debug('img_ratio %s', img_ratio)
    if asptect_ratio_change_threshold is not None:
        asptect_ratio_change_threshold_percentage = asptect_ratio_change_threshold/100
        log.debug('asptect_ratio_change_threshold %s is not None', asptect_ratio_change_threshold)
        if ratio > img_ratio:
            log.debug('ratio %s is > img_ratio %s', ratio, img_ratio)
            image_ratio_threshold_adjusted = img_ratio + asptect_ratio_change_threshold_percentage
            if image_ratio_threshold_adjusted >= ratio:
                log.debug('image_ratio_threshold_adjusted %s is >= ratio %s', image_ratio_threshold_adjusted, ratio)
                ratio = img_ratio
            else:
                log.debug('image_ratio_threshold_adjusted %s is not >= ratio %s', image_ratio_threshold_adjusted, ratio)
        elif ratio < img_ratio:
            image_ratio_threshold_adjusted = img_ratio - asptect_ratio_change_threshold_percentage
            if image_ratio_threshold_adjusted <= ratio:
                log.debug('image_ratio_threshold_adjusted %s is <= ratio %s', image_ratio_threshold_adjusted, ratio)
                ratio = img_ratio
            else:
                log.debug('image_ratio_threshold_adjusted %s is not <= ratio %s', image_ratio_threshold_adjusted, ratio)
    else:
        log.debug('asptect_ratio_change_threshold %s is None', asptect_ratio_change_threshold)

    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], int(round(size[0] * img.size[1] / img.size[0]))),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, int(round((img.size[1] - size[1]) / 2)), img.size[0],
                   int(round((img.size[1] + size[1]) / 2)))
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((int(round(size[1] * img.size[0] / img.size[1])), size[1]),
                         Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = (int(round((img.size[0] - size[0]) / 2)), 0,
                   int(round((img.size[0] + size[0]) / 2)), img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]),
                         Image.ANTIALIAS)
    # If the scale is the same, we do not need to crop
    return img


def download_and_resize_image(keep_downloads, download_path, width, height, url=None, crop_type='middle'):
    """Check to see if the raw image has allready been downloaded

        Args:
            | download_path (string): full path to the filename to save the image as
            | width (string): width of the image to be resized to
            | height (string): height of the image to be resized to
            | url=None (string): url of the image
            | height (string): the first part of the filename
            | crop_type='middle' (string): crop type can be middle top bottom

        Returns:
            obj: <class 'PIL.Image.Image'> or None if image cannot be made

    """
    return_image = None
    if os.path.isfile(download_path):
        try:
            Image.open(download_path)
        except:
            download(url, download_path)
    else:
        download(url, download_path)

    if os.path.isfile(download_path):
        temp_image = Image.open(download_path)
        temp_image_width, temp_image_height = temp_image.size
        if temp_image_width == width and temp_image_height == height:
            return_image = temp_image.copy()
            temp_image.close()
        else:
            return_image = resize_and_crop(download_path, (width, height), crop_type)
            temp_image.close()
        if not keep_downloads:
            os.remove(download_path)
            log.debug('Deleted {0}'.format(download_path))
    return return_image


def save_image(img, extension, smbcon=None, **kwargs):
    log.debug('Saving compiled image {0} for kwargs: {1}'.format(
        kwargs['image_save_path'],
        kwargs))
    if extension.lower() not in ['png']:
        img = img.convert('RGB')
    if kwargs['dune_render_store_dict']['type'] == 'local':
        img.save(kwargs['image_save_path'])
    elif kwargs['dune_render_store_dict']['type'] == 'smb':
        # smbcon = smbfs(dune_render_store_dict['connection_dict'])
        file_obj = tempfile.NamedTemporaryFile()
        img.seek(0)
        img.save(file_obj, kwargs['image_extension'])
        # seek to start of file for writting
        file_obj.seek(0)
        smbcon.storeFile(kwargs['image_save_path'], file_obj)
        file_obj.close()
    # smbcon.close()
    log.debug('Saved compiled image {0} for kwargs: {1}'.format(
        kwargs['image_save_path'],
        kwargs))
    return True
