# -*- coding:utf-8 -*-
#!/usr/bin/env python

import time

def service_main():
    while True:
        print('Hello,xapp!')
        time.sleep(10)

if __name__ == '__main__':
    service_main()