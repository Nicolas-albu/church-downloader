import os
import tempfile

import streamlit as st
import yt_dlp
from streamlit.delta_generator import DeltaGenerator


def download(url: str, progress_bar: DeltaGenerator, status_text: DeltaGenerator) -> str:
    def progress_hook(data: dict):
        if data['status'] == 'downloading':
            downloaded = data.get('downloaded_bytes', 0)

            if total := data.get('total_bytes') or data.get('total_bytes_estimate'):
                progress = min(downloaded / total, 1.0)

                if speed := data.get('speed'):
                    speed_text = (
                        f'{speed / (1024 * 1024):.2f} MB/s'
                        if speed >= 1024 * 1024
                        else f'{speed / 1024:.2f} KB/s'
                    )
                else:
                    speed_text = 'calculando...'

                if eta := data.get('eta'):
                    minutes, seconds = divmod(eta, 60)
                    eta_text = (
                        f'{minutes}m {seconds}s restantes'
                        if minutes
                        else f'{seconds}s restantes'
                    )
                else:
                    eta_text = 'calculando...'

                progress_bar.progress(value=progress, text=f'{progress * 100:.1f}%')
                status_text.text(f'{speed_text} | {eta_text}')

        elif data['status'] == 'finished':
            progress_bar.progress(
                value=1.0, text='Download concluído. Processando vídeo...'
            )
            status_text.text('Preparando arquivo final...')

    folder = tempfile.mkdtemp()
    options = {
        'format': 'bestvideo*+bestaudio/best',
        'merge_output_format': 'mkv',
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'embedthumbnail': True,
        'addmetadata': True,
        'restrictfilenames': False,
        'progress_hooks': [progress_hook],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url=url, download=True)
        filename = ydl.prepare_filename(info)

    # O merge pode transformar o arquivo final em MKV.
    if info.get('requested_formats'):
        filename = os.path.splitext(filename)[0] + '.mkv'
    return filename


st.title('Downloader da IASD Central Coruripe')

url = st.text_input(
    label='Adicione o link do vídeo aqui:', placeholder='URL do vídeo do YouTube'
)

if url.strip():
    progress_bar = st.progress(value=0, text='Preparando o download...')
    status_text = st.empty()

    try:
        filename = download(url, progress_bar, status_text)

        with open(filename, 'rb') as file:
            data = file.read()

        progress_bar.progress(value=1.0, text='Download concluído!')
        status_text.text(filename)
        st.success('Download concluído.')

        st.download_button(
            label='Baixar vídeo',
            data=data,
            file_name=os.path.basename(filename),
            mime='video/x-matroska',
            type='primary',
            on_click='ignore',
        )

    except Exception as error: # noqa
        progress_bar.empty()
        status_text.empty()
        st.error(f'Erro ao baixar o vídeo: {error}')
