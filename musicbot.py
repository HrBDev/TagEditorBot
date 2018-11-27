# coding: utf-8
import logging

import eyed3
import requests
import telebot
from eyed3.id3 import Tag
from eyed3.mp3 import Mp3AudioFile
from requests import Response
from telebot.types import InlineKeyboardButton
from telegram import Message, File

token = <Your Token Here> 
tb = telebot.TeleBot(token)

logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)  # Outputs debug messages to console.


@tb.message_handler(commands=['start'])
def handle_start(message):
    tb.send_message(chat_id=message.chat.id, text="Welcome to Music Tag Bot!")


@tb.message_handler(commands=['help'])
def handle_help(message):
    tb.send_message(chat_id=message.chat.id,
                    text="This bot will let you edit tags of your mp3 files,send an mp3 file and try it out!")


@tb.message_handler(content_types=['audio'])
def handle_audio(message):
    # Download uploaded file from telegram server
    file_info = tb.get_file(message.audio.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path))
    filename = message.audio.file_id + ".mp3"
    open(str(filename), 'wb').write(file.content)

    tag_editor = TagEditor(filename)
    tag_editor.send_audio_info(message.chat.id)


@tb.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data
    if data.startswith('done'):
        tb.send_document(call.message.chat.id, open(data.split('-')[1], 'rb'))
    else:
        tag_editor = TagEditor(data.split('-')[2])
        if data.startswith('set-title'):
            msg = tb.send_message(call.message.chat.id, "Send song title:")
            tb.register_next_step_handler(msg, tag_editor.set_title)
        if data.startswith('set-artist'):
            msg = tb.send_message(call.message.chat.id, "Send song artist:")
            tb.register_next_step_handler(msg, tag_editor.set_album)
        if data.startswith('set-album'):
            msg = tb.send_message(call.message.chat.id, "Send song album:")
            tb.register_next_step_handler(msg, tag_editor.set_artist)
        if data.startswith('set-aalbum-'):
            msg = tb.send_message(call.message.chat.id, "Send album artist:")
            tb.register_next_step_handler(msg, tag_editor.set_album_artist)
        if data.startswith('set-disk-'):
            msg = tb.send_message(call.message.chat.id, "Send disk number:")
            tb.register_next_step_handler(msg, tag_editor.set_disk_num)
        if data.startswith('set-track-'):
            msg = tb.send_message(call.message.chat.id, "Send track number:")
            tb.register_next_step_handler(msg, tag_editor.set_track_num)
        if data.startswith('set-image-'):
            msg = tb.send_message(call.message.chat.id, "Send image file:")
            tb.register_next_step_handler(msg, tag_editor.set_image)
    tb.answer_callback_query(call.id)


class TagEditor:
    def __init__(self, filename):
        self.filename = filename
        self.audio = eyed3.load(filename)

    def set_title(self, message):
        self.audio.tag.title = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_album(self, message):
        self.audio.tag.album_artist = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_artist(self, message):
        self.audio.tag.artist = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_track_num(self, message):
        self.audio.tag.track_num = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_album_artist(self, message):
        self.audio.tag.album_artist = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_disk_num(self, message):
        self.audio.tag.disc_num = message.text
        self.audio.tag.save()
        self.send_audio_info(message.chat.id)

    def set_image(self):
        self.audio.tag.images.set("image/jpeg", u"Discription",
                                  img_url='https://t2.genius.com/unsafe/220x220/https%3A%2F%2Fimages.genius.com%2F6d33231676683ef18a688e21b0d2c943.630x630x1.jpg')
        self.audio.tag.save()

    def send_audio_info(self, chat_id):
        tag = self.audio.tag
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton('Title', callback_data='set-title-' + self.filename),
            InlineKeyboardButton('Artist', callback_data='set-artist-' + self.filename),
            InlineKeyboardButton('Album', callback_data='set-album-' + self.filename)
        )
        keyboard.row(
            InlineKeyboardButton('Album Artist', callback_data='set-aalbum-' + self.filename),
            InlineKeyboardButton('Disk#', callback_data='set-disk-' + self.filename),
            InlineKeyboardButton('Track#', callback_data='set-track-' + self.filename)
        )
        keyboard.row(
            InlineKeyboardButton('Image', callback_data='set-image-' + self.filename)
        )
        keyboard.row(
            InlineKeyboardButton('done', callback_data='done-' + self.filename)
        )
        tb.send_message(chat_id=chat_id, text="Title: " + str(tag.title) + "\n" +
                                              "Artist: " + str(tag.artist) + "\n" +
                                              "Album: " + str(tag.album) + "\n" +
                                              "Album Artist: " + str(tag.album_artist) + "\n" +
                                              "Disk#: " + str(tag.disc_num) + "\n" +
                                              "Track#: " + str(tag.track_num),
                        reply_markup=keyboard)


tb.polling(none_stop=True, interval=0, timeout=20)
