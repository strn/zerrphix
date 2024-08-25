class tmdb(object):
    def __init__(self):
        self.eapi_name = 'tmdb'
        self._supported_source_eapi_ = {'film': {'want': 'imdb', 'have': 'tmdb'},
                                        'tv': {'want': ['imdb'], 'have': ['tmdb']}}

    def acquire_external_eid(self, eapi_have, eapi_have_eid, library):
        return_dict = {}
        return_dict['imdb'] = 666
        # return_dict['thetvdb'] = 333
        return return_dict


class tvmaze(object):
    def __init__(self):
        self.eapi_name = 'tvmaze'
        self._supported_source_eapi_ = {'film': {'want': 'imdb', 'have': 'tmdb'},
                                        'tv': {'want': ['tvmaze', 'thetvdb'], 'have': ['imdb']}}

    def acquire_external_eid(self, eapi_have, eapi_have_eid, library):
        return_dict = {}
        return_dict['thetvdb'] = 548
        # return_dict['thetvdb'] = 333
        return return_dict


def check_for_missing_eapi_eid(eapi_dict_got):
    for eapi in eapi_dict_got:
        if eapi_dict_got[eapi] is None:
            return True
    return False


def check_exhausted_eapi_lookup(eapi_dict, eapi_access_list):
    # eapi_dict_to_get_hash = md5(str(eapi_dict['to_get'])).hexdigest()
    for eapi in eapi_access_list:
        for eapi_to_get in eapi_dict['to_get']:
            print('eapi_to_get %s' % eapi_to_get)
            if eapi_dict['to_get'][eapi_to_get] is None:
                for eapi_checked in eapi_dict['checked']:
                    print('eapi_checked %s' % eapi_checked)
                    if eapi_to_get != eapi_checked:
                        print(eapi, eapi_dict['checked'][eapi_to_get])
                        if eapi not in eapi_dict['checked'][eapi_to_get]:
                            print('''eapi %s not in eapi_dict['checked'][eapi_to_get] %s''' % (
                            eapi, eapi_dict['checked'][eapi_to_get]))
                            return False
                            # elif eapi_dict_to_get_hash not in eapi_dict['checked'][eapi_to_get][eapi]:
                        #	print('''eapi_dict_to_get_hash %s not in eapi_dict['checked'][eapi_to_get][eapi] %s''' % (eapi_dict_to_get_hash, eapi_dict['checked'][eapi_to_get][eapi]))
                        #	return False
                    else:
                        print('eapi_to_get %s = eapi_checked %s' % (eapi_to_get, eapi_checked))
    return True


def get_eapi_eid(eapi_dict, library, eapi_init):
    eapi_to_lookup_list = []
    processing_complete = False
    for eapi_to_get in eapi_dict['to_get']:
        print('eapi_to_get %s' % eapi_to_get)
        if eapi_dict['to_get'][eapi_to_get] is None:
            print('''eapi_dict['to_get'][eapi_to_get] %s is None''' % eapi_dict['to_get'][eapi_to_get])
            if eapi_to_get not in eapi_dict['checked'][eapi_init.eapi_name]:
                print('eapi_to_get %s not in checked %s' % (eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name]))
                if eapi_to_get in eapi_init._supported_source_eapi_[library]['want']:
                    print(
                    'eapi_to_get %s in want %s' % (eapi_to_get, eapi_init._supported_source_eapi_[library]['want']))
                    for eapi_have in eapi_dict['to_get']:
                        if eapi_dict['to_get'][eapi_have] is not None:
                            if eapi_have in eapi_init._supported_source_eapi_[library]['have']:
                                eapi_to_lookup_list.append({'eapi': eapi_have, 'eid': eapi_dict['to_get'][eapi_have]})
                                # if eapi
                                print('adding eapi_to_get %s to checked for eapi_have %s %s' % (
                                eapi_to_get, eapi_have, eapi_dict['to_get']))
                                eapi_dict['checked'][eapi_init.eapi_name].append(eapi_to_get)
                            else:
                                print(
                                '''eapi_have %s not in eapi_init._supported_source_eapi_[library]['have'] %s''' % (
                                eapi_have, eapi_init._supported_source_eapi_[library]['have']))
                        else:
                            print('''eapi_dict['to_get'][eapi_have] %s is None''' % eapi_dict['to_get'][eapi_have])
                else:
                    print(
                    'eapi_to_get %s not in want %s' % (eapi_to_get, eapi_init._supported_source_eapi_[library]['want']))
            else:
                print('eapi_to_get %s in checked %s' % (eapi_to_get, eapi_dict['checked'][eapi_init.eapi_name]))
        else:
            print('''eapi_dict['to_get'][eapi_to_get] %s is NOT None''' % eapi_dict['to_get'][eapi_to_get])

    print('Ctmdb', eapi_dict, eapi_to_lookup_list)
    return process_eapi_dict(eapi_to_lookup_list, eapi_dict, library)


def process_eapi_dict(eapi_to_lookup_list, eapi_dict, library, eapi_init):
    for eapi_to_lookup in eapi_to_lookup_list:
        print(eapi_to_lookup)
        eapi_acquired_dict = eapi_init.acquire_external_eid(eapi_to_lookup['eapi'], eapi_to_lookup['eid'], library)
        print(eapi_acquired_dict)
        for eapi_acquired in eapi_acquired_dict:
            print(eapi_acquired)
            if eapi_dict['to_get'][eapi_acquired] is None:
                eapi_dict['to_get'][eapi_acquired] = eapi_acquired_dict[eapi_acquired]
    return eapi_dict


def combination_check(eapi_dict, eapi_access_list):
    # eapi_dict_hash = md5(eapi_dict).hexdigest()
    new_conbination_tried = False
    keep_looking = True
    while new_conbination_tried is False:
        for eapi_to_get in eapi_dict['to_get']:
            print('main', eapi_to_get)
            if eapi_dict['to_get'][eapi_to_get] is None:
                print('''eapi_dict['to_get'][eapi_to_get] %s is None''' % eapi_dict['to_get'][eapi_to_get])
                for eapi in eapi_access_list:
                    print('now using eapi %s' % eapi)
                    # eapi_eapi_to_get_md5 = md5('%s%s' % (eapi, eapi_to_get)).hexdigest()
                    combination = '%s|%s' % (eapi, eapi_to_get)
                    if eapi not in eapi_dict['checked'][eapi_to_get] and combination not in eapi_dict[
                        'cominations_tried']:
                        print(
                        '''eapi %s not in eapi_dict['checked'][eapi_to_get] %s and eapi_eapi_to_get_md5 %s not in eapi_dict['cominations_tried'] %s''' % (
                        eapi, eapi_dict['checked'][eapi_to_get], eapi, eapi_dict['cominations_tried']))
                        print(eapi_dict)
                        # eapi_dict['checked'][eapi_to_get][eapi] = []
                        # eapi_init = globals()[eapi]().get_eapi_eid(eapi_dict, 'tv')
                        eapi_init = globals()[eapi]()
                        eapi_dict = get_eapi_eid(eapi_dict, 'tv', eapi_init)
                        print('using %s to get %s - %s' % (eapi, eapi_to_get, eapi_dict))
                        eapi_dict['cominations_tried'].append(combination)
                        new_conbination_tried = True
                        # eapi_dict
                        print(
                        '''eapi %s eapi_dict['checked'][eapi_to_get] %s ''' % (eapi, eapi_dict['checked'][eapi_to_get]))
                        print(eapi_dict)
                        # raise SystemExit
                    else:
                        print()

        print('not combinations left to try')
        keep_looking = False
        new_conbination_tried = True

    return eapi_dict, keep_looking


if __name__ == "__main__":

    eapi_access_list = ['tvmaze', 'tmdb']

    eapi_dict = {}
    eapi_dict['to_get'] = {}
    eapi_dict['to_get']['tmdb'] = 123
    eapi_dict['to_get']['imdb'] = None
    eapi_dict['to_get']['tvmaze'] = None
    eapi_dict['to_get']['thetvdb'] = None

    eapi_dict['checked'] = {}
    eapi_dict['checked']['thetvdb'] = []
    eapi_dict['checked']['imdb'] = []
    eapi_dict['checked']['tvmaze'] = []
    eapi_dict['checked']['tmdb'] = []

    eapi_dict['cominations_tried'] = []
    keep_looking = True

    while keep_looking is True:
        print('keep_looking')
        if check_for_missing_eapi_eid(eapi_dict['to_get']) is False:
            print('found all eapi eids')
            keep_looking = False
        else:
            print('not all found %s' % eapi_dict['to_get'])
            if check_exhausted_eapi_lookup(eapi_dict, eapi_access_list) is False:
                print('Not exhausted exhausted_eapi_lookup')
                eapi_dict, keep_looking = combination_check(eapi_dict, eapi_access_list)
                # time.sleep(1)
            else:
                print('exhausted all eapis %s' % eapi_dict['checked'])
                keep_looking = False
