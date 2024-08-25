from __future__ import unicode_literals, division, absolute_import, print_function

import logging
import math

log = logging.getLogger(__name__)


def seconds_to_hours(seconds):
    s = seconds
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)


def get_rating_image_number(db_rating, rating_max):
    max_db_rating = 10
    #print('rating_max %s' % rating_max)
    rating_10 = max_db_rating / rating_max
    #print('rating_10 %s' % rating_10)
    for rating in range(1, rating_max + 1):
        # print('range %s out of %s' % (rataing_step, rating))
        min = int(math.floor((rating - 1) * rating_10) + 1)
        max = int(math.floor(rating * rating_10))
        if db_rating >= min and db_rating <= max:
            return rating

def is_even(num):
    return num % 2 == 0
