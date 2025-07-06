import asyncio
import ssl
import xml.etree.ElementTree as ET
import argparse
from tqdm.asyncio import tqdm_asyncio

async def check_article(session_id, semaphore, server_config, article_id):
    """
    Connects to the Usenet server and checks for a single article's existence.
    Returns the article_id and a boolean indicating if it was found.
    """
    host, port, username, password, use_ssl = server_config
    
    try:
        async with semaphore:
            # Establish connection
            ssl_context = ssl.create_default_context() if use_ssl else None
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=ssl_context),
                timeout=15
            )

            # Read initial welcome message
            await reader.read(1024)

            # Authenticate
            if username:
                writer.write(f"AUTHINFO USER {username}\r\n".encode())
                await writer.drain()
                await reader.read(1024) # Server response
                writer.write(f"AUTHINFO PASS {password}\r\n".encode())
                await writer.drain()
                await reader.read(1024) # Server response

            # Check for article existence with STAT command
            writer.write(f"STAT <{article_id}>\r\n".encode())
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(1024), timeout=15)
            
            # Close the connection
            writer.write(b"QUIT\r\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            
            # 223 means the article exists. 430 means it does not.
            if response.startswith(b"223"):
                return article_id, True
            else:
                return article_id, False

    except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
        # Handle connection errors or timeouts
        return article_id, None # None indicates an error
    except Exception as e:
        return article_id, None


def parse_nzb(nzb_path):
    """Parses an NZB file and returns a list of all article IDs."""
    try:
        tree = ET.parse(nzb_path)
        root = tree.getroot()
        # NZB files use a namespace, which we need to handle
        namespace = {'nzb': 'http://www.newzbin.com/DTD/2003/nzb'}
        article_ids = [
            segment.text
            for segment in root.findall(".//nzb:segment", namespace)
        ]
        return list(set(article_ids)) # Return unique IDs
    except ET.ParseError:
        print(f"Error: Could not parse '{nzb_path}'. Is it a valid XML/NZB file?")
        return []
    except FileNotFoundError:
        print(f"Error: File not found at '{nzb_path}'")
        return []

async def main(args):
    """Main function to orchestrate the checking process."""
    server_config = (
        args.server,
        args.port,
        args.username,
        args.password,
        not args.no_ssl
    )
    
    print(f"[*] Parsing NZB file: {args.nzb_file}")
    article_ids = parse_nzb(args.nzb_file)
    
    if not article_ids:
        print("[!] No article IDs found in the NZB file. Exiting.")
        return

    total_articles = len(article_ids)
    print(f"[*] Found {total_articles} unique articles to check.")
    print(f"[*] Starting check with {args.connections} concurrent connections...")

    semaphore = asyncio.Semaphore(args.connections)
    tasks = [
        check_article(i, semaphore, server_config, article_id)
        for i, article_id in enumerate(article_ids)
    ]

    results = []
    # Use tqdm for a nice progress bar
    for future in tqdm_asyncio.as_completed(tasks, total=total_articles):
        result = await future
        results.append(result)

    found_count = 0
    missing_count = 0
    error_count = 0
    missing_articles = []

    for article_id, status in results:
        if status is True:
            found_count += 1
        elif status is False:
            missing_count += 1
            missing_articles.append(article_id)
        else:
            error_count += 1

    print("\n--- Check Complete ---")
    print(f"Total Articles: {total_articles}")
    print(f"  \033[92mFound: {found_count}\033[0m") # Green text
    print(f"  \033[91mMissing: {missing_count}\033[0m") # Red text
    if error_count > 0:
        print(f"  \033[93mErrors (Timeouts/Connection Failed): {error_count}\033[0m") # Yellow text

    completion_percentage = (found_count / total_articles) * 100 if total_articles > 0 else 0
    print(f"Completion Rate: {completion_percentage:.2f}%")

    if missing_count > 0 and args.show_missing:
        print("\n--- Missing Article IDs ---")
        for article_id in missing_articles:
            print(article_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A fast, concurrent Usenet NZB completion checker."
    )
    parser.add_argument("nzb_file", help="Path to the .nzb file to check.")
    parser.add_argument("-s", "--server", required=True, help="Usenet server address (e.g., news.your-provider.com).")
    parser.add_argument("-p", "--port", type=int, default=563, help="Server port (default: 563 for SSL).")
    parser.add_argument("-u", "--username", help="Your Usenet username.")
    parser.add_argument("-pw", "--password", help="Your Usenet password.")
    parser.add_argument("-c", "--connections", type=int, default=50, help="Number of concurrent connections to use (default: 50).")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL for the connection (e.g., for port 119).")
    parser.add_argument("--show-missing", action="store_true", help="Print the list of all missing article IDs at the end.")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\n[!] Script interrupted by user. Exiting.")
