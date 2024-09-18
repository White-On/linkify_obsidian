import sys
from pathlib import Path


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


def main():
    nb_args = len(sys.argv)
    obsidian_script_used = nb_args == 3
    no_specified_file = None
    note_titles = None
    safe_mode = True

    if obsidian_script_used:
        vault_path = Path(sys.argv[1])
        file_path = vault_path / sys.argv[2]

        if not vault_path.exists():
            print(f"Vault path does not exist: {vault_path}")
            return
        if not file_path.exists():
            print(f"Parsing file does not exist: {file_path}")
            return
        no_specified_file = not file_path.is_file()
        if no_specified_file:
            print(f"No Specific file given, all files in the vault will be linkify")
            files_to_unbacklink = get_markdown_files(vault_path)
        else:
            print(f'Running linkify script on "{file_path.stem}"')
            files_to_unbacklink = [file_path]

        for file in files_to_unbacklink:
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(file, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line.replace("[[", "").replace("]]", ""))

        print("Done")
    else:
        print("Usage with obsidian script")


if __name__ == "__main__":
    main()
