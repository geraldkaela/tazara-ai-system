import sys
import importlib.util

def main():
    print('executable=', sys.executable)
    print('version=', sys.version)
    print('find_spec(numpy)=', importlib.util.find_spec('numpy'))

if __name__ == '__main__':
    main()
