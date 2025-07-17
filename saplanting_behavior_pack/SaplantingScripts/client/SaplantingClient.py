# -*- coding: utf-8 -*-
from random import random

import mod.client.extraClientApi as clientApi

from .BaseClientSystem import BaseClientSystem
from ..config.heyconfig import ClientSetting
from ..config.sapling import default_saplings
from ..util.common import Singleton
from ..util.listen import Listen

compFactory = clientApi.GetEngineCompFactory()
engineName = clientApi.GetEngineNamespace()
engineSystem = clientApi.GetEngineSystemName()


class ClientMasterSetting(object):
    __metaclass__ = Singleton
    wait_time_range = 5
    check_time_range = 15

    def __init__(self):
        """
        初始化树苗枚举和最小等待时间
        """
        self.saplings = default_saplings
        self.min_wait_time = 3
        self.check_min_wait_time = 15 + self.min_wait_time

    def load_config(self, data):
        """
        从配置数据中加载树苗枚举和最小等待时间
        """
        if "saplings" in data:
            self.saplings = set(tuple(value) for value in data["saplings"])
        if "min_wait_time" in data:
            self.min_wait_time = max(0, data["min_wait_time"])
            self.check_min_wait_time = 15 + self.min_wait_time

    def get_wait_time(self):
        """
        获取随机等待时间
        """
        return random() * self.wait_time_range + self.min_wait_time

    def get_check_wait_time(self):
        """
        获取随机检查等待时间
        """
        return random() * self.check_time_range + self.check_min_wait_time


class SaplantingClient(BaseClientSystem):
    def __init__(self, namespace, name):
        super(SaplantingClient, self).__init__(namespace, name)
        """
        创建游戏组件并初始化设置
        """
        self.game_comp = compFactory.CreateGame(self.levelId)
        self.master_setting = ClientMasterSetting()
        self.item_entities = {}
        self.client_setting = ClientSetting()

    @Listen.on("LoadClientAddonScriptsAfter")
    def on_enabled(self, event=None):
        """
        加载客户端设置并注册配置
        """
        self.client_setting.load()
        comp = clientApi.CreateComponent(self.levelId, "HeyPixel", "Config")
        if comp:
            from ..config.heyconfig import register_config
            comp.register_config(register_config)

    @Listen.on("UiInitFinished")
    def on_local_player_stop_loading(self, event=None):
        """
        同步玩家砍树状态到服务器
        """
        self.NotifyToServer("SyncPlayerTreeFallingState", {"playerId": self.playerId, "state": self.client_setting.tree_felling})

    def reload_client_setting(self):
        """
        重新加载客户端设置并同步到服务器
        """
        self.client_setting.load()
        self.NotifyToServer("SyncPlayerTreeFallingState", {"playerId": self.playerId, "state": self.client_setting.tree_felling})

    @Listen.server("SyncMasterSetting")
    def on_sync_master_setting(self, data):
        """ 
        同步主设置
        """
        self.master_setting.load_config(data)

    @Listen.on("AddEntityClientEvent")
    def on_add_sapling_item(self, event):
        # todo 已知event的文档如右侧连接 ：    https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E4%BA%8B%E4%BB%B6/%E4%B8%96%E7%95%8C.html?key=AddEntityClientEvent&docindex=2&type=0
        # todo 已存在 self.master_setting.saplings 为树苗的枚举
        """
        监听添加实体事件，判断是否为树苗
        """
        if "itemName" in event:
            # 请继续完成此方法的判断
            if event["itemName"] in self.master_setting.saplings:
                entityId = event["id"]
                self.item_entities[entityId] = (event["itemName"], event["auxValue"])
                self.game_comp.AddTimer(self.master_setting.get_check_wait_time(), self.check_on_ground, entityId)

    @Listen.on("RemoveEntityClientEvent")
    def on_remove_entity(self, event):
        """
        监听移除实体事件，从字典中移除对应的实体
        """
        entityId = event["id"]
        if entityId in self.item_entities:
            self.item_entities.pop(entityId)

    @Listen.on("OnGroundClientEvent")
    def on_sapling_on_ground(self, event):
        """
        监听实体落地事件，判断是否为树苗
        """
        entityId = event["id"]
        if entityId in self.item_entities:
            self.game_comp.AddTimer(self.master_setting.get_wait_time(), self.on_ground_notify, entityId)

    def on_ground_notify(self, entityId):
        """
        通知服务器树苗落地
        """
        if entityId in self.item_entities:
            itemName, auxValue = self.item_entities[entityId]
            # print "notify sapling item on ground", entityId
            self.NotifyToServer("onSaplingOnGround", {"playerId": self.playerId, "entityId": entityId, "itemName": itemName, "auxValue": auxValue})

    def check_on_ground(self, entityId):
        """
        检查实体是否落地，若未落地则继续检查
        """
        if entityId in self.item_entities:
            if compFactory.CreateAttr(entityId).isEntityOnGround():
                self.on_ground_notify(entityId)
            else:
                self.game_comp.AddTimer(self.master_setting.get_check_wait_time(), self.check_on_ground, entityId)

    def reload_master_setting(self):
        """
        重新加载主设置并通知服务器
        """
        self.NotifyToServer("ReloadMasterSetting", {})
