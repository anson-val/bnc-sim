from network.network import LineNetwork

def main():
    LineNetwork(256, 10, 10, 10).feed_file("test.txt")  


if __name__ == "__main__":
    main()
