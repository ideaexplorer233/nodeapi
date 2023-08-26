from typing import Dict
import aiofiles
from aiofiles import os
from aiofiles.threadpool.text import AsyncTextIOWrapper


async def prepare_dir():
    await os.makedirs("notes", exist_ok=True)


class FileManager:
    def __init__(self):
        self.files: Dict[str, AsyncTextIOWrapper] = {}
        self.occupation: Dict[str, int] = {}

    async def open(self, filename: str):
        if filename not in self.files:
            self.files[filename] = await aiofiles.open("notes/" + filename, "r+")
            self.occupation[filename] = 1
        else:
            self.occupation[filename] += 1

    async def close(self, filename: str):
        if self.occupation[filename] == 1:
            await self.files.pop(filename).close()
            del self.occupation[filename]
        else:
            self.occupation[filename] -= 1
