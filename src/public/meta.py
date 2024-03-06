
from src.common.meta import *


class PublicItemAdd(ConfigMetaClass):
    env_id = MustInteger('env_id')
    key = Base64Decode('key')
    value = Base64Decode('value')
    
    def __init__(self, *args, **kwargs) -> None:
        self.env_id = kwargs.get('env_id')
        self.key = kwargs.get('key')
        self.value = kwargs.get('value')
        
        super().__init__(*args, **kwargs)


class PublicItemInfo(ConfigMetaClass):
    public_item_id = MustInteger('public_item_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.public_item_id = kwargs.get('id')
        
        super().__init__(*args, **kwargs)


class PublicItemVersionInfo(PublicItemInfo): pass


class PublicItemVersionUpdate(ConfigMetaClass):
    public_item_id = MustInteger('public_item_id')
    version_id = MustInteger('version_id')
    key = Base64Decode('key')
    value = Base64Decode('value')
    
    def __init__(self, *args, **kwargs) -> None:
        self.public_item_id = kwargs.get('id')
        self.version_id = kwargs.get('version_id')
        self.key = kwargs.get('key')
        self.value = kwargs.get('value')
        
        super().__init__(*args, **kwargs)


class PublicItemPublish(ConfigMetaClass):
    public_item_id = MustInteger('public_item_id')
    version_id = MustInteger('version_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.public_item_id = kwargs.get('id')
        self.version_id = kwargs.get('version_id')
        
        super().__init__(*args, **kwargs)


class PublicItemRollback(PublicItemPublish): pass


class PublicItemDelete(ConfigMetaClass):
    public_item_ids = list()

    def __init__(self, *args, **kwargs) -> None:
        self.public_item_ids = kwargs.get('public_item_ids')
        
        super().__init__(*args, **kwargs)

class PublicItemVersionRecord(ConfigMetaClass):
    public_item_version_id = MustInteger('public_item_version_id')
    name = MustString('name')
    k = MustString('k')
    v = MustString('v')
    env_id = MustInteger('env_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.public_item_version_id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.k = kwargs.get('k')
        self.v = kwargs.get('v')
        self.env_id = kwargs.get('env_id')
        
        super().__init__(*args, **kwargs)

class PublicItemVersionRelatedGeneralPublish(ConfigMetaClass):
    public_item_version_id = MustInteger('public_item_version_id')
    related_general_list = list()
    
    def __init__(self, *args, **kwargs) -> None:
        self.public_item_version_id = kwargs.get('public_item_version_id')
        self.related_general_list = kwargs.get('related_general_list')

        super().__init__(*args, **kwargs)
