from wsgidav.wsgidav_app import WsgiDAVApp
from cheroot.wsgi import Server as WsgiServer

CONFIG = {
    # ------------------------------------------------------------
    # WebDAV ROOT
    # Expose ONLY /users as the WebDAV root
    # This is REQUIRED for FolderSync compatibility
    # ------------------------------------------------------------
    "provider_mapping": {
        "/": {
            "root": "/mnt/orion-nas/users"
        }
    },

    # ------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------
    "simple_dc": {
        "user_mapping": {
            "*": {
                "praveen_flip": {"password": "praveen"},
                "ruchi_realme": {"password": "ruchi"},
            }
        }
    },

    # ------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------
    "logging": {
        "enable": True,
        "file": "/home/orion/server/services/webdav/logs/webdav.log",
    },

    # ------------------------------------------------------------
    # Verbosity
    # ------------------------------------------------------------
    "verbose": 1,
}

if __name__ == "__main__":
    app = WsgiDAVApp(CONFIG)
    server = WsgiServer(
        ("0.0.0.0", 8081),
        app,
    )
    server.start()
