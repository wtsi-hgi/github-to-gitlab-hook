from bottle import LocalRequest, LocalResponse, Bottle

from server.examples.bottle_wrapper import create_app
from server.examples.wsgi_server import WsgiServerController

HELLO_WORLD_TEXT = "Hello World!"


def hello(request: LocalRequest, response: LocalResponse) -> str:
    return HELLO_WORLD_TEXT


def create_example_app() -> Bottle:
    app = create_app({
        "/": hello
    })
    return app


def run_example_app():
    app = create_example_app()
    server_controller = WsgiServerController(app, port=8080)
    server_controller.run()


if __name__ == "__main__":
    run_example_app()
