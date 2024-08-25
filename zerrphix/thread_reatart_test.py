import time
import threading
import traceback

def fail():
    raise TypeError('some type error')

def start_thread():
    dunehttpserver_thread = threading.Thread(target=fail, name='dhtpThread', args=ss)
    dunehttpserver_thread.start()


if __name__ == "__main__":

    try:
        fail()
    except Exception as e:
        #print(e)
        print(traceback.print_exc())
        #raise

    if 1 == 2:
        def threadwrap(threadfunc):
            def wrapper():
                while True:
                    try:
                        threadfunc()
                    except BaseException as e:
                        print('{!r}; restarting thread'.format(e))
                    else:
                        print('exited normally, bad thread; restarting')

            return wrapper


        thread_dict = {
            'a': threading.Thread(target=wrapper(a), name='a'),
            'b': threading.Thread(target=wrapper(b), name='b')
        }

        while True:
            time.sleep(30)