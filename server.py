from networking.server import MudServer


def main():
    server = MudServer(host='0.0.0.0', port=4000)
    server.start()

if __name__ == "__main__":
    main()
