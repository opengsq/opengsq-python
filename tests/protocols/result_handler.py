import json
import os
import asyncio
from pathlib import Path


class ResultHandler:
    enable_save = False
    delay_per_test = 0
    results_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'results')

    def __init__(self, protocol_name):
        "ResultHandler"
        self.__protocol_path = os.path.join(self.results_path, protocol_name)
        Path(self.__protocol_path).mkdir(exist_ok=True)

    async def save_result(self, function_name, result, is_json=True):
        "Save and print the result"
        
        if self.enable_save:
            if is_json:
                result = json.dumps(result, indent=4, ensure_ascii=False)
            
            with open(os.path.join(self.__protocol_path, f'{function_name}.{(is_json and "json" or "txt")}'), 'w', encoding='utf-8') as f:
                print(result, file=f)
            
        await asyncio.sleep(self.delay_per_test)
