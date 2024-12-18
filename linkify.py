import sys
import re
import logging
import unicodedata

from pathlib import Path


def get_note_titles(vault_path: Path) -> list[str]:
    """
    Reads note titles from the Obsidian vault.
    Assuming each note's title is its filename without the extension.
    Excludes dot folders like .obsidian.
    """
    markdown_files = get_markdown_files(vault_path)
    note_titles = [file.stem for file in markdown_files]
    return note_titles


def get_markdown_files(vault_path: Path) -> list[Path]:
    """
    Get all markdown files in the vault.
    """
    markdown_files = list(vault_path.glob("**/*.md"))
    # filter out dot folders like .obsidian
    # both for Unix and Windows paths
    markdown_files = [
        file
        for file in markdown_files
        if not "/." in str(file) and not "\." in str(file)
    ]
    return markdown_files


def separate_acronyms_and_classic_titles(
    titles: list[str],
) -> tuple[list[str], list[str]]:
    """
    Separates note titles into two lists: acronyms and classic titles.
    Acronyms are only uppercase letters.
    """
    acronyms = {}
    classic_titles = []
    for title in titles:
        classic_titles.append(title)
        # transform the title into a accronym
        simpler_title = simplified_string(title)
        potential_acronym = "".join(
            [word[0].upper() for word in simpler_title.split("_")]
        )
        if len(potential_acronym) > 1 and potential_acronym not in acronyms:
            acronyms[potential_acronym] = title

    logging.debug(f"🔠 Acronyms: {acronyms}")
    logging.debug(f"📚 Classic titles: {classic_titles}")

    return acronyms, classic_titles


def split_text_for_linkification(text: str) -> list[tuple[str, bool]]:
    """
    Some sections of the text should not be linkified.
    This is especially the case with math blocks, and code blocks.
    This function splits the text into linkifiable and non-linkifiable sections.
    """
    # Split the text into sections that should be linkified and those that should not
    split_text = re.split(
        r'''
        (```.*?```                     # Code blocks (```...```)
        |(?<!`)\$\$.*?\$\$             # Multiline math blocks ($$...$$)
        |(?<!`)\$.*?\$                 # Inline math blocks ($...$)
        |^\|.*\|$                      # Table rows starting and ending with |
        )
    ''', text, flags= re.VERBOSE | re.MULTILINE | re.DOTALL)

    # Keep track of whether each section should be linkified
    linkifiable_sections = []
    for i, section in enumerate(split_text):
        # Sections that should not be linkified are math blocks, code blocks and tables
        linkifiable = not (section.startswith("```") or section.startswith("$") or section.startswith("|"))
        linkifiable_sections.append((section, linkifiable))

    return linkifiable_sections


def linkify_text(text: str, note_titles: list[str], file_title=None) -> tuple[str, int]:
    """
    Replaces occurrences of note titles in the text with [[note-title]] links.
    Prefers the longest match.
    """
    # we remove the file title from the note titles to avoid linking to the current file
    if file_title:
        note_titles = [title for title in note_titles if title != file_title]

    # We need to distinguish the classic note title from acronyms note titles
    # Acronyms are only uppercase letters, and replacement should be done with the same case
    acronyms, classic_titles = separate_acronyms_and_classic_titles(note_titles)

    # Sort titles by length in descending order to prefer longest match
    sorted_titles = sorted(classic_titles, key=len, reverse=True)
    nb_new_links = 0

    def replacement(match, title=None):
        original_text = match.group(0)

        # don't modify the text if it's already a link
        if "[[" in original_text or "]]" in original_text:
            return original_text
        else:
            # Check if the matched text ends with 's', include it in the link if not
            if (
                original_text.lower().endswith("s")
                and original_text[:-1] in sorted_titles
            ):
                linkified = f"[[{original_text[:-1]}]]s"
            else:
                if title and title != original_text:
                    linkified = f"[[{title}|{original_text}]]"
                else:
                    linkified = f"[[{original_text}]]"

            nonlocal nb_new_links
            nb_new_links += 1
            return linkified

    # Escape titles for regex, add word boundaries, and handle an optional 's' at the end
    # example: (\b|\[\[)TODO(\B|\]\])
    # example V2: (\b|\[\[)TODOs?(\]\])?s?(?![\w])
    decoration_start = r"(\b|\[\[)"
    decoration_end = r"s?(\]\])?s?(?![\w])"

    # a dict to store the title and the pattern
    pattern_collection = {
        title: decoration_start + re.escape(title) + decoration_end
        for title in sorted_titles
    }

    # Use a regex to replace titles in the text with their linkified versions
    linked_text = text
    for title, pattern in pattern_collection.items():
        logging.debug(f"Title: {title}, Pattern: {pattern}")
        linked_text = re.sub(
            pattern,
            lambda match: replacement(match, title),
            linked_text,
            flags=re.IGNORECASE,
        )

    if len(acronyms) == 0:
        return linked_text

    # Handle acronyms separately because they don't need word boundaries in the same way
    logging.debug(f"Acronyms: {acronyms}")
    acronyms_pattern_collection = {
        acronym: decoration_start + acronym + decoration_end
        for acronym in acronyms.keys()
    }
    # logging.debug(f"Pattern acronyms: {acronyms_pattern_collection}")
    for acronym, pattern, title in zip(
        acronyms.keys(), acronyms_pattern_collection.values(), acronyms.values()
    ):
        logging.debug(f"Acronym: {acronym}, Pattern: {pattern}, Title: {title}")
        linked_text = re.sub(
            pattern, lambda match: replacement(match, title), linked_text, re.IGNORECASE
        )

    return linked_text, nb_new_links


def simplified_string(s: str) -> str:
    """
    Simplifies a string by removing accents, converting to lowercase, and replacing spaces with underscores.
    """
    s = remove_accents(s).decode("utf-8")
    return s.casefold().replace(" ", "_").replace("-", "_")


def remove_accents(input_str: str) -> bytes:
    """
    Removes accents from a string.
    """
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    only_ascii = nfkd_form.encode("ASCII", "ignore")
    return only_ascii


def setup_logging(log_filename: Path = None):
    """
    Set up logging to a file and the console.
    """

    if log_filename is None:
        log_filename = Path("linkify.log")
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def copy_files_to_somewhere_else(destination: Path, *files: list[Path], **kwargs):
    """
    Copy files to a destination folder.
    """

    for file in files:
        try:
            file_name = file.name
            destination_file = destination / file_name
            if destination_file.exists():
                logging.debug(f"🔴 File already exists: {destination_file}")
                continue
            with open(file, "r", **kwargs) as f:
                text = f.read()
            with open(destination_file, "w", **kwargs) as f:
                f.write(text)
            logging.debug(f"📋 Copied file: {destination_file}")
        except Exception as e:
            logging.error(f"🔴 Error copying file {file}: {e}")
            print(f"Error copying file {file}: {e}")


def main():
    log_filename = Path(__file__).stem + ".log"
    setup_logging(log_filename)

    nb_args = len(sys.argv)

    obsidian_script_used = nb_args == 3
    no_specified_file = None
    note_titles = None
    safe_mode = True

    if obsidian_script_used:
        python_script = sys.argv[0]
        vault_path = Path(sys.argv[1])
        file_path = vault_path / sys.argv[2]

        logging.debug(f"python_script: {python_script}")
        logging.debug(f"📂 Vault path: {vault_path.absolute()}")
        logging.debug(f"📋 Parsing file: {file_path}")

        if not vault_path.exists():
            logging.error(f"🔴 Vault path does not exist: {vault_path}")
            print(f"Vault path does not exist: {vault_path}")
            return
        if not file_path.exists():
            logging.error(f"🔴 Parsing file does not exist: {file_path}")
            print(f"Parsing file does not exist: {file_path}")
            return
        no_specified_file = not file_path.is_file()
        if no_specified_file:
            logging.warning(
                f"🔴 No Specific file given, all files in the vault will be linkify"
            )
            print(f"No Specific file given, all files in the vault will be linkify")
            files_to_linkify_path = get_markdown_files(vault_path)
        else:
            print(f'Running linkify script on "{file_path.stem}"')
            files_to_linkify_path = [file_path]

        note_titles = get_note_titles(vault_path)
        if not note_titles:
            logging.error(f"🔴 No markdown files found in the vault: {vault_path}")
            print(f"No markdown files found in the vault: {vault_path}")
            return

        # to ensure the safety of the integrity of the vault we will
        # make a dir as a backup of the files that will be modified
        if safe_mode:
            safe_dir = f"backup_{vault_path.stem}"
            safe_filepath = vault_path.parent / safe_dir
            safe_filepath.mkdir(exist_ok=True)

            logging.info(f"📂 Safe directory: {safe_filepath}")
            print(f"Safe mode enabled, backup files will be stored in {safe_filepath}")
            copy_files_to_somewhere_else(
                safe_filepath, *files_to_linkify_path, encoding="utf-8"
            )

        logging.info(f"📚 Nb note titles: %s", len(note_titles))
        nb_new_backlinks = 0
        for file_to_linkify_path in files_to_linkify_path:
            try:
                with open(file_to_linkify_path, "r", encoding="utf-8") as file:
                    text = file.read()

                file_title = Path(file_to_linkify_path).stem
                linkifiable_sections = split_text_for_linkification(text)
                complete_linked_text = ""
                for section, linkifiable in linkifiable_sections:
                    if linkifiable:
                        linked_text, nb_new_links = linkify_text(
                            section, note_titles, file_title
                        )
                        complete_linked_text += linked_text
                        nb_new_backlinks += nb_new_links
                    else:
                        complete_linked_text += section
                new_file_path = vault_path / file_to_linkify_path.name
                with open(new_file_path, "w", encoding="utf-8") as file:
                    file.write(complete_linked_text)

                logging.debug(f"🔗 Linkified file: {file_to_linkify_path.stem}")
            except Exception as e:
                logging.error(
                    f"🔴 Error processing file {file_to_linkify_path.stem}: {e}"
                )
                print(f"Error processing file {file_to_linkify_path.stem}: {e}")

        logging.info(f"🔗 Total new backlinks: {nb_new_backlinks}")
        print(f"Script executed successfully")
        print(f"Total new backlinks: {nb_new_backlinks}")
    else:
        # Test mode
        note_titles = ["Regression", "Supervised learning", "Machine learning"]

        logging.warning("🔧 Running in test mode")
        logging.info(f"📚 Nb note titles: %s", len(note_titles))

        test_text = "The goal of **regression** or function approximation is to create a model from observed data. The model has \
            a fixed structure with parameters (such as the coefficients of a polynomial), and regression involves adjusting these \
            parameters to fit the data. In Machine learning, this is a crucial technique as having a good model leads to better \
            predictions and performance. Regression is part of [[Supervised learning|supervised learning]] methods. ML algorithms that are used for regression\
            are called regression algorithms. And what a bout a french word like régression?"

        logging.info("Note titles: %s", note_titles)

        linked_text, nb_added_backlink = linkify_text(
            test_text, note_titles, "Regression"
        )
        logging.info("Linkified test text: %s", linked_text)
        logging.info("Nb new backlinks: %s", nb_added_backlink)


if __name__ == "__main__":
    main()
