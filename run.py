import sys
from transfer_subscriptions import main_transfer_subscriptions
from transfer_playlists import main_transfer_playlists

def main():
    print("Which content would you like to transfer?")
    print("1. Subscriptions")
    print("2. Playlists")
    print("3. Both")
    choice = input("Enter the number (1, 2, or 3): ")

    if choice == '1':
        main_transfer_subscriptions()
    elif choice == '2':
        main_transfer_playlists()
    elif choice == '3':
        print("Transferring subscriptions...")
        main_transfer_subscriptions()
        print("Transferring playlists...")
        main_transfer_playlists()
    else:
        print("Invalid input. Exiting.")
        sys.exit()

if __name__ == "__main__":
    main()
