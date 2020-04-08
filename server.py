import asyncio
from asyncio import transports


history_message = []
user_names = []

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login in user_names:
                        self.transport.write(f"Логин {self.login} занят, попробуйте другой\n".encode())
                        self.server.clients.remove(self.login)
                else:
                    user_names.append(self.login)
                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
                self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        user_names.remove(self.login)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        for user in self.server.clients:
            user.transport.write(message.encode())
        history_message.append(f"{self.login}: {content}\n")

    def send_history(self):
        if len(history_message) > 10:
            for message in history_message[-10:]:
                self.transport.write(message.encode())
        elif len(history_message) > 0:
            for message in history_message:
                self.transport.write(message.encode())

class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            9999
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
