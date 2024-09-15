import time
import sys

import click
from dotenv import dotenv_values

from services.api_client import APIClient, APIClientException

config = dotenv_values(".env")


API_KEY = None
SERVER = None

@click.group()
@click.option('--api_key', help='Users api_key.', default=config.get("DENET_API_KEY"))
@click.option('--server', help='SERVER URL', default=config.get("DENET_SERVER"))
def cli(api_key:str, server:str):
    global API_KEY
    global SERVER
    API_KEY = api_key
    SERVER = server
    if API_KEY and SERVER:
        click.echo(f"Connection to {SERVER}:{API_KEY}")
    else:
        click.echo(f"Your environment is not setup. Сonfigure it or use --api_key and --server directly.")
        time.sleep(2)
        sys.exit(1)


@click.command()
def ls():
    """ Show storage list """
    click.echo(f'List of your storage in server {SERVER}')
    client = APIClient(server=SERVER, api_key=API_KEY)
    try:
        storage_list = client.storage_list().get("storage_list")
    except APIClientException as err:
        click.echo(f"Couldn't connect to server {repr(err)}")
        time.sleep(2)
        sys.exit(1)
    if storage_list:
        for number, storage in enumerate(storage_list):
            file_name = storage.get("name")
            pk = storage.get("id")
            click.echo(f"{number + 1}) ID={pk}, {file_name=} ")


@click.command()
@click.option('--path', help='Path for save', default=".", type=click.Path(file_okay=False))
@click.argument("storage_id")
def download(path:str, storage_id: int):
    """ Download file from storage by ID"""
    click.echo(f'{path=}')
    click.echo(f'Download file by ID={storage_id} in server {SERVER}')
    client = APIClient(server=SERVER, api_key=API_KEY)
    try:
        download = client.download(storage_id, path)
    except APIClientException as err:
        click.echo(f"Couldn't connect to server {repr(err)}")
        time.sleep(2)
        sys.exit(1)
    click.echo(f'File was downloaded')


@click.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False))
def upload(file:str):
    """ Upload file to storage """
    click.echo(f'Upload file {file} to server')
    client = APIClient(server=SERVER, api_key=API_KEY)
    try:
        upload = client.upload_file(file)
    except APIClientException as err:
        click.echo(f"Couldn't connect to server {repr(err)}")
        time.sleep(2)
        sys.exit(1)
    click.echo(f'File was uploaded')


@click.command()
@click.argument('name', type=str)
def register(name:str):
    """ Upload file to storage """
    click.echo(f'Register {name} in server')
    client = APIClient(server=SERVER, api_key=API_KEY)
    try:
        upload = client.upload_file(file)
    except APIClientException as err:
        click.echo(f"Couldn't connect to server {repr(err)}")
        time.sleep(2)
        sys.exit(1)
    click.echo(f'File was uploaded')


cli.add_command(ls)
cli.add_command(download)
cli.add_command(upload)


if __name__ == '__main__':
    cli()