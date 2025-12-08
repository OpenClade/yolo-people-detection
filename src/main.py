import ultralytics


def main():
    yolo = ultralytics.YOLO("./models/yolo11n.pt")
    print('hello world')



if __name__ == "__main__":
    main()
