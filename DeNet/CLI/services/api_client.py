import os.path
import pathlib
import asyncio

import aiofiles
import aiohttp
import requests


class Status:

    def __init__(self, status=0):
        self.__status = status

    def increment(self):
        self.__status += 1

    def get(self):
        return self.__status


class APIClientException(Exception):
    pass

class APIClient:

    endpoints = {
        "storage": "/storage",
        "download_cell": "/download",
        "download_init": "/download_init",
        "upload": "/upload_init",
        "upload_cell": "/upload",
        "register": "/register",
    }

    def __init__(self, server, api_key):
        self.server = server
        self.api_key = api_key

    def _get_api_key_header(self):
        return {"api-key": self.api_key}


    def _get_endpoint(self, endpoint:str):
        return self.server + self.endpoints.get(endpoint)


    def upload_file(self, path):
        path = pathlib.Path(path)
        name = path.name
        file_size = os.path.getsize(path)
        size = file_size //1024 //1024
        if os.path.getsize(path) % 1024 % 1024 != 0:
            size += 1
        upload_init = self._get_upload_session(size, name)
        upload_session = upload_init.get("session")

        results = self._upload_run(upload_session, path, size)
        wrong_addresses = []
        for result in results:
            address, status = result
            if status != 201:
                wrong_addresses.append(address)
        if wrong_addresses:
            raise APIClientException(f"Couldn't upload: {wrong_addresses}")
        pass

    def _upload_run(self, upload_session, path, size):
        res = asyncio.run(self._async_upload(upload_session, path, size))
        return res


    async def _async_upload(self, upload_session, path, size):
        file_gen = self._split_file(path)
        tasks = []
        name = path.name
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
            for i in range(size):
                address, data = await file_gen.__anext__()
                task = self._upload_task(client, upload_session, address, name, data)
                tasks.append(task)
            # tasks = [write_to_disk(path, address, data) for i in range(12)]
            return await asyncio.gather(*tasks)


    async def _upload_task(self, client, upload_session, address, file_name, file_data):
        headers = self._get_api_key_header()
        headers["session"] = upload_session

        content_type = "application/octet-stream"
        data = aiohttp.FormData()
        data.add_field(
            name="file",
            value=file_data,
            filename=file_name,
            content_type=content_type,
        )
        data.add_field(
            name="number",
            value=str(address)
        )

        async with client.post(self._get_endpoint("upload_cell"), headers=headers, data=data, ssl=False) as response:
            # print(response.status)
            # result = await response.read()
            return address, response.status


    async def _split_file(self, file_path):
        address = 0
        async with aiofiles.open(file_path, mode='rb') as f:
            data = await f.read(1024 * 1024)
            address = 0
            while data:
                # async with aiofiles.open("file", mode='wb') as f:
                #     await f.write(data)
                yield address, data
                data = await f.read(1024 * 1024)
                address += 1


    def _get_upload_session(self, size, name):
        result = requests.post(
            url=self._get_endpoint("upload"),
            headers=self._get_api_key_header(),
            json={"size": size, "name": name}
        )
        if result.status_code != 201:
            raise APIClientException("The server rejected the request for upload session")
        return result.json()

    def download(self, storage_id, save_path):
        storage:dict = self._download_init(storage_id)
        file_name = storage.get("name")
        size = int(storage.get("size"))
        cells = storage.get("cells")
        if size != len(cells):
            raise Exception("file is not OK!")
        status = Status(0)
        result = self._download_run(size, cells, save_path, status)
        if False in result:
            raise APIClientException("Couldn't download this file. The server rejected request.")
        self._compose_file(size, file_name, save_path)
        return storage


    def _download_run(self, size, cells, save_path, status):
        res = asyncio.run(self._async_download(size, cells, save_path, status))
        return res


    async def _async_download(self, size, cells, save_path, status):
        tasks = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
            for cell in cells:
                task = self._download_cell(client, cell, save_path, status)
                tasks.append(task)
            return await asyncio.gather(*tasks)


    async def _download_cell(self, client, cell, save_path, status):
        headers = self._get_api_key_header()
        url = cell.get("path")
        address = cell.get("address")

        async with client.get(self._get_endpoint("download_cell") + "/" + url,
                               headers=headers) as response:
            if response.status == 200:
                result = await response.read()
                await self._write_to_disk(result, address, save_path)
                status.increment()
                status.increment()
                return True
            else:
                return False


    async def _write_to_disk(self, content: bytes, id: int, save_path:str):
        file_path = "{}/{}".format(save_path, id)
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(content)


    def _download_init(self, storage_id):
        result = requests.get(
            url=self._get_endpoint("download_init"),
            headers=self._get_api_key_header(),
            json={"id": storage_id}
        )
        if result.status_code != 200:
            raise APIClientException(f"The server rejected the request for storage ID={storage_id}")
        return result.json()


    def storage_list(self):
        result = requests.get(url=self._get_endpoint("storage"), headers=self._get_api_key_header())
        if result.status_code != 200:
            raise APIClientException(f"The server rejected the request for storage list")
        return result.json()


    def _compose_file(self, size, file_name, path):
        with open(f'{path}/{file_name}', "wb") as file:
            for i in range(size):
                try:
                    with open(f'{path}/{i}', "rb") as r_file:
                        content = r_file.read()
                        file.write(content)
                    os.remove(f'{path}/{i}')
                except FileExistsError:
                    raise APIClientException(f"No this file {size}")


    def register(self, name):
        result = requests.post(
            url=self._get_endpoint("register"),
            json={"api_key": self.api_key, "name": name}
        )
        if result != 201:
            raise APIClientException(f"The server rejected the request for registry. Probably wrong api-key")
        return result.json()
