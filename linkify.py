import sys
import os
import re
import logging
import unicodedata

from urllib.parse import quote  # for url encoding
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
    acronyms = []
    classic_titles = []
    for title in titles:
        if title.isupper():
            acronyms.append(title)
        else:
            classic_titles.append(title)

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
        r"(```.*?```|(?<!`)\$\$.*?\$\$|(?<!`)\$.*?\$)", text, flags=re.DOTALL
    )

    # Keep track of whether each section should be linkified
    linkifiable_sections = []
    for i, section in enumerate(split_text):
        # Sections that should not be linkified are math blocks and code blocks
        linkifiable = not (section.startswith("```") or section.startswith("$"))
        linkifiable_sections.append((section, linkifiable))

    return linkifiable_sections


def linkify_text(text: str, note_titles: list[str], file_title=None) -> str:
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
                if title:
                    linkified = f"[[{title}|{original_text}]]"
                else:
                    linkified = f"[[{original_text}]]"
            return linkified

    # Escape titles for regex, add word boundaries, and handle an optional 's' at the end
    # example: (\b|\[\[)TODO(\B|\]\])
    # example V2: (\b|\[\[)TODOs?(\]\])?s?(?![\w])
    decoration_start = r"(\b|\[\[)"
    decoration_end = r"s?(\]\])?s?(?![\w])"

    # a dict to store the title and the pattern
    pattern_collection = {
        title: decoration_start
        + re.escape(remove_accents(title).decode("utf-8"))
        + decoration_end
        for title in sorted_titles
    }
    logging.debug(f"Pattern collection: {pattern_collection}")

    no_accent_text = remove_accents(text).decode("utf-8")
    # Use a regex to replace titles in the text with their linkified versions
    linked_text = text
    for title, pattern in pattern_collection.items():
        linked_text = re.sub(
            pattern,
            lambda match: replacement(match, title),
            linked_text,
            flags=re.IGNORECASE,
        )

    # Handle acronyms separately because they don't need word boundaries in the same way
    acronyms_pattern = "|".join(
        decoration_start + re.escape(acronym) + decoration_end for acronym in acronyms
    )
    logging.debug(f"Pattern acronyms: {acronyms_pattern}")
    linked_text = re.sub(acronyms_pattern, replacement, linked_text)

    return linked_text


def simplified_string(s):
    s = remove_accents(s).decode("utf-8")
    print(s)
    return s.casefold().replace(" ", "_").replace("-", "_")


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    only_ascii = nfkd_form.encode("ASCII", "ignore")
    return only_ascii


def setup_logging(log_filename: Path = None):

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


def main():

    log_filename = Path(__file__).stem + ".log"
    setup_logging(log_filename)

    nb_args = len(sys.argv)

    obsidian_script_used = nb_args == 3
    no_specified_file = None
    note_titles = None

    if obsidian_script_used:
        python_script = sys.argv[0]
        vault_path = Path(sys.argv[1])
        file_path = vault_path / sys.argv[2]

        logging.info(f"python_script: {python_script}")
        logging.info(f"📂 Vault path: {vault_path.absolute()}")
        logging.info(f"📋 Parsing file: {file_path}")

        if not vault_path.exists():
            logging.error(f"🔴 Vault path does not exist: {vault_path}")
            return
        if not file_path.exists():
            logging.error(f"🔴 Parsing file does not exist: {file_path}")
            return
        no_specified_file = not file_path.is_file()
        if no_specified_file:
            logging.warning(
                f"🔴 No Specific file given, all files in the vault will be linkify"
            )

        note_titles = get_note_titles(vault_path)
        if not note_titles:
            logging.error(f"🔴 No markdown files found in the vault: {vault_path}")
            return

        # to ensure the safety of the integrity of the vault we will
        # make a dir inside the vault to store the linkified files
        # so we don't mess up with the original files if something goes wrong
        safe_dir = "linkified_files"
        safe_filepath = vault_path / safe_dir
        safe_filepath.mkdir(exist_ok=True)

        if no_specified_file:
            parsing_filepath = get_markdown_files(vault_path)
        else:
            parsing_filepath = [file_path]

        files_to_linkify_path = parsing_filepath

        logging.info(f"📂 Vault path: {vault_path.absolute()}")
        logging.info(f"📚 Nb note titles: %s", len(note_titles))
        for file_to_linkify_path in files_to_linkify_path:
            try:
                with open(file_to_linkify_path, "r") as file:
                    text = file.read()

                file_title = Path(file_to_linkify_path).stem
                linkifiable_sections = split_text_for_linkification(text)
                complete_linked_text = ""
                for section, linkifiable in linkifiable_sections:
                    if linkifiable:
                        linked_text = linkify_text(section, note_titles, file_title)
                        complete_linked_text += linked_text
                    else:
                        complete_linked_text += section
                new_file_path = safe_filepath / file_to_linkify_path.name
                with open(new_file_path, "w") as file:
                    file.write(complete_linked_text)

                logging.info(f"🔗 Linkified file: {file_to_linkify_path.stem}")
            except Exception as e:
                logging.error(
                    f"🔴 Error processing file {file_to_linkify_path.stem}: {e}"
                )
    else:
        # test mode
        logging.info("🔧 Running in test mode")
        return
        logging.info(f"📂 Vault path: {vault_path.absolute()}")
        logging.info(f"📚 Nb note titles: %s", len(note_titles))

        test_text = "L'objectif de la **régression** ou de l'approximation de la fonction est de créer un modèle à partir des données observées. \
            Le modèle a une structure fixe avec des paramètres (comme les coefficients d'un polynôme par exemple), et la régression consiste à ajuster \
            ces paramètres pour s'adapter aux données. En machine learning, c'est une technique très importante car avoir un bon modèle permet de \
            meilleures prédictions et performances. La régression fait parti des méthode d'supervised learning"

        logging.info("Note titles: %s", note_titles)

        linked_text = linkify_text(test_text, note_titles, "Regression")
        logging.info("Linkified test text: %s", linked_text)


if __name__ == "__main__":
    main()
