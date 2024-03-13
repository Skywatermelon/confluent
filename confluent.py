import os
from atlassian import Confluence
import html2text
import configparser
import shutil
from datetime import datetime

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def print_progress_bar(iteration, total, current_file, total_errors, length=50):
    percent = "{0:.1f}".format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = '#' * filled_length + '-' * (length - filled_length)
    
    clear_screen()
    print(f'Progress: |{bar}| {percent}% Complete')
    print(f'Current File: {current_file}')
    print(f'Total Errors: {total_errors}')

def fetch_and_convert_pages(config, download_path):
    base_url = config['Confluence']['base_url']
    username = config['Confluence']['username']
    password = config['Confluence']['password']

    confluence = Confluence(
        url=base_url,
        username=username,
        password=password
    )

    cql = "type=page and space='{space_key}'".format(space_key=config['Confluence']['space_key'])
    pages = confluence.cql(cql, limit=1000)['results']

    print(f"Total number of pages fetched: {len(pages)}")

    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    space_folder = f"{config['Confluence']['space_key']}-{current_time}"
    space_folder = os.path.join(download_path, space_folder)
    os.makedirs(space_folder, exist_ok=True)

    errors = []
    total_errors = 0

    for i, page in enumerate(pages):
        
        page_title = "Untitled"  # Default title
        try:
            # Check for correct key based on actual data structure
            page_id = page.get('id') or page.get('content', {}).get('id')
            if not page_id:
                raise ValueError("Page ID not found.")

            page_title = page.get('title', 'Untitled').replace('/', '_').replace(' ', '_')

            page_data = confluence.get_page_by_id(page_id, expand='body.storage')
            page_content = page_data['body']['storage']['value']

            h = html2text.HTML2Text()
            h.ignore_images = True
            markdown_content = h.handle(page_content)

            md_file_name = f"{page_title}.md"
            md_file_path = os.path.join(space_folder, md_file_name)
            with open(md_file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(markdown_content)
        except Exception as e:
            error_message = f"Failed to process page '{page_title}': {e}"
            errors.append(error_message)
            total_errors += 1

        print_progress_bar(i + 1, len(pages), page_title, total_errors)

    # Print errors at the end if there are any
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(error)

if __name__ == '__main__':
    config_file = 'config.ini'
    config = read_config(config_file)
    download_path = os.path.expanduser('~/Downloads/confluent')
    fetch_and_convert_pages(config, download_path)
