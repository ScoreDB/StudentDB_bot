from telegram.ext import Dispatcher

from ._callback import callback_handler
from ._error import error_handler
from ._inline import inline_search_handler
from .auth import auth_handler, input_token_handler
from .help import help_handler
from .search import command_search_handler, message_search_handler
from .start import start_handler


def register_commands(dispatcher: Dispatcher):
    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(help_handler)

    dispatcher.add_handler(auth_handler)
    dispatcher.add_handler(input_token_handler)

    dispatcher.add_handler(command_search_handler)
    dispatcher.add_handler(message_search_handler)

    dispatcher.add_handler(inline_search_handler)

    dispatcher.add_handler(callback_handler)

    dispatcher.add_error_handler(error_handler)
