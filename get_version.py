def get_version():
    f = open("version.txt")
    print(f.read())

if __name__ == "__main__":
    get_version()