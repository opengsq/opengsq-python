import asyncio
import json
import os
from pathlib import Path


class ResultHandler:
    enable_save = False
    delay_per_test = 0

    def __init__(self, pathname: str):
        "ResultHandler"

        self.file_name = os.path.splitext(os.path.basename(pathname))[
            0
        ]  # Returns: 'test_ase'
        self.last_dir = os.path.basename(
            os.path.dirname(pathname)
        )  # Returns: 'protocols'

        # docs/tests/protocols/
        self.results_path = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__), "..", "docs", "tests", self.last_dir
            )
        )
        Path(self.results_path).mkdir(exist_ok=True)

        # docs/tests/protocols/test_ase/
        self.__protocol_path = os.path.join(self.results_path, self.file_name)
        Path(self.__protocol_path).mkdir(exist_ok=True)

        self.create_tests_index_rst()

    async def save_result(self, function_name, result, is_json=True):
        "Save and print the result"

        if self.enable_save:
            if is_json:
                result = json.dumps(
                    result, indent=4, ensure_ascii=False, default=lambda o: o.__dict__
                )

            # with open(os.path.join(self.__protocol_path, f'{function_name}.{(is_json and "json" or "txt")}'), 'w', encoding='utf-8') as f:
            #     print(result, file=f)

            with open(
                os.path.join(self.__protocol_path, f"{function_name}.rst"),
                "w",
                encoding="utf-8",
            ) as f:
                title = function_name
                f.write(title + "\n")
                f.write(("=" * len(title)) + "\n")
                f.write("\nHere are the results for the test method.\n")
                f.write(f'\n.. code-block:: {(is_json and "json" or "text")}\n\n')

                for line in result.splitlines():
                    f.write("\t" + line + "\n")

            self.create_tests_protocols_index_rst()

        await asyncio.sleep(self.delay_per_test)

    def create_tests_index_rst(self):
        test_files = Path(os.path.join(os.path.dirname(__file__), self.last_dir)).glob("test_*.py")

        with open(
            os.path.join(self.results_path, "index.rst"), "w", encoding="utf-8"
        ) as f:
            title = self.last_dir.title().replace("_", " ") + ' Tests'
            f.write(".. _tests:\n")
            f.write(f"\n{title}\n")
            f.write(f'{"=" * len(title)}\n')
            f.write("\n.. toctree::\n")

            for file in test_files:
                f.write(f"\t{file.name[:-3]}/index\n")

    def create_tests_protocols_index_rst(self):
        test_results_files = Path(self.__protocol_path).glob("test_*.rst")

        with open(
            os.path.join(self.__protocol_path, "index.rst"), "w", encoding="utf-8"
        ) as f:
            f.write(f".. _{self.file_name}:\n")
            f.write(f"\n{self.file_name}\n")
            f.write(f'{"=" * len(self.file_name)}\n')
            f.write("\n.. toctree::\n")

            for file in test_results_files:
                f.write(f"\t{file.name[:-4]}\n")
