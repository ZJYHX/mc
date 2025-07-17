# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
from mod.common.mod import Mod

from .config.modConfig import *


@Mod.Binding(name=ModName, version=ModVersion)
class SaplantingMod(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    # 初始化服务器
    def server_init(self):
        # 注册系统
        serverApi.RegisterSystem(ModName, ServerSystemName, ServerSystemClsPath)

    @Mod.InitClient()
    # 初始化客户端
    def client_init(self):
        # 注册系统
        clientApi.RegisterSystem(ModName, ClientSystemName, ClientSystemClsPath)

    @Mod.DestroyClient()
    # 定义一个销毁客户端的方法
    def destroy_client(self):
        pass

    @Mod.DestroyServer()
    # 定义一个销毁服务器的函数
    def destroy_server(self):
        pass
