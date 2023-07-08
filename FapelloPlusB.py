import os
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
import multiprocessing




def create_directory():
    while True:
        try: 
            directory = input("Enter the name of the directory: ")
            parent_dir = os.getcwd()
            path = os.path.join(parent_dir, directory)
            os.mkdir(path)
            print(f"Directory '{directory}' created.")
            break
        except FileExistsError:
                print(f"Directory {directory} already exists.")
    return directory


def get_last_photo():
    headers = {"User-Agent": UserAgent(use_external_data=True).random}
    while True:
        name = input("Enter the username: ")
        url = f"https://fapello.com/{name}/"
        response = requests.get(url, headers=headers, allow_redirects=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "lxml")
            pattern = soup.find("div", {"id": "content"}).find("div")
            photo_id = pattern.find("a").attrs["href"]
            url_pattern = pattern.find("img").attrs["src"].rsplit("/", 2)[0]
            return url_pattern, photo_id.rsplit("/", 3)[2], name
        else:
            print("User not found! Try again.")


def download_image(session, url, header, directory):
    response = session.get(url, headers=header, allow_redirects=True)
    if response.status_code == 200:
        file_name = url.rsplit("/", 1)[1]
        with open(f"{directory}/{file_name}", "wb") as f:
            f.write(response.content)
    else:
        print(f"Photo unavailable: {url}")


def download_chunk(*args):
    URL, chunk, session, header, directory, in_range = args
    c = 1
    start_id, end_id = chunk
    if start_id <= 999:
        c = 1
    elif start_id % 1000 == 0:
        print("You're lucky!")
    else:
        c = int(str(start_id)[0]) + 1
    for imageID in range(start_id, end_id, in_range):
        url = f"{URL[0]}/{c}000/{URL[2]}_{str(imageID).zfill(4)}.jpg"
        if imageID % 1000 == 0:
            if in_range == 1:
                c += 1
            else:
                c -= 1
        download_image(session, url, header, directory)


def download_new_or_missed_photos(*args):
    URL, chunk, session, header, directory, start_range, end_range = args
    not_existing_files = 0
    start_range, end_range = chunk
    for imageID in tqdm(range(start_range, end_range)):
        c = (imageID // 1000) + 1
        url = f"{URL[0]}/{c}000/{URL[2]}_{str(imageID).zfill(4)}.jpg"
        file_name = url.rsplit("/", 1)[1]
        if os.path.exists(f"./{directory}/{file_name}"):
            continue
        else:
            not_existing_files += 1
            download_image(session, url, header, directory)
    print(f"New files: {not_existing_files}")


def chunk_loader(args):
    (
        URL,
        session,
        header,
        directory,
        num_processors,
        start_range,
        end_range,
        in_range,
        choice,
    ) = args

    # Calculate the chunk size based on the number of processors
    chunk_size = (end_range - start_range) // num_processors

    # Create a list of chunk boundaries
    chunks = [
        (start_range + i * chunk_size, start_range + (i + 1) * chunk_size)
        for i in range(num_processors)
    ]
    chunks[-1] = (chunks[-1][0], end_range)  # Adjust the last chunk's end ID

    # Create a multiprocessing Pool
    pool = multiprocessing.Pool(processes=num_processors)

    # Map the chunks to worker processes
    results = []
    if choice == "1" or choice == "3":
        for chunk in chunks:
            results.append(
                pool.apply_async(
                    download_chunk,
                    args=(URL, chunk, session, header, directory, in_range),
                )
            )
    elif choice == "2":
        for chunk in chunks:
            results.append(
                pool.apply_async(
                    download_new_or_missed_photos,
                    args=(
                        URL,
                        chunk,
                        session,
                        header,
                        directory,
                        start_range,
                        end_range,
                    ),
                )
            )

    # Wait for all processes to finish
    pool.close()
    pool.join()

    # Check for any exceptions
    for result in results:
        result.get()  # Raise an exception if occurred


def main():
    if __name__ == "__main__":
        URL = get_last_photo()
        header = {"User-Agent": UserAgent(use_external_data=True).random}
        session = requests.Session()
        choice = input(
            "Which type of function do you want to use? "
            "1. Download all photos, "
            "2. Download new photos or missed, "
            "3. Download photos in a range: "
        )
        while True:
            cpu_count = multiprocessing.cpu_count()
            try:
                num_processors = int(input("Enter the number of processors to use: "))
                if num_processors <= cpu_count:
                    break
                else:
                    print(f"You don't have that much CPU, You have only: {cpu_count}")
            except:
                print("Something went wrong when")

        if choice in ["1", "2", "3"]:
            if choice == "2":
                directory = input("Enter the existing folder name: ")
            else:
                directory = create_directory()

            if choice == "1":
                start_range = int(URL[1])
                end_range = 1
                in_range = -1
            else:
                start_range = int(input("Enter the starting photo ID: "))
                end_range = int(input("Enter the ending photo ID: ")) + 1
                in_range = 1

            chunk_loader(
                args=(
                    URL,
                    session,
                    header,
                    directory,
                    num_processors,
                    start_range,
                    end_range,
                    in_range,
                    choice,
                )
            )
        else:
            print(f"Invalid function choice: {choice}")

        session.close()


if __name__ == "__main__":
    main()
