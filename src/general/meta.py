from src.common.meta import *


class GeneralAdd(ConfigMetaClass):
    name = NonBlank('name')
    env_id = MustInteger('env_id')
    belongto = MustString('belongto')
    content = Base64Decode('content')
    
    def __init__(self, *args, **kwargs) -> None:
        self.name = kwargs.get('name')
        self.env_id = kwargs.get('env_id')
        self.belongto = kwargs.get('belongto')
        self.content = kwargs.get('content')
        
        super().__init__(*args, **kwargs)


class GeneralInfo(ConfigMetaClass):
    general_id = MustInteger('general_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('id')
        
        super().__init__(*args, **kwargs)


class GeneralVersionInfo(GeneralInfo): pass


class GeneralVersionUpdate(ConfigMetaClass):
    general_id = MustInteger('general_id')
    version_id = MustInteger('version_id')
    content = Base64Decode('content')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('general_id')
        self.version_id = kwargs.get('version_id')
        self.content = kwargs.get('content')
        
        super().__init__(*args, **kwargs)


class GeneralVersionAbandon(ConfigMetaClass):
    general_id = MustInteger('general_id')
    version_id = MustInteger('version_id')
    status = MustString('status')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('general_id')
        self.version_id = kwargs.get('id')
        self.status = kwargs.get('status')


class GeneralPublish(ConfigMetaClass):
    general_id = MustInteger('general_id')
    version_id = MustInteger('version_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('general_id')
        self.version_id = kwargs.get('version_id')
        
        super().__init__(*args, **kwargs)


class GeneralRollback(GeneralPublish): pass


class GeneralPermission(ConfigMetaClass):
    general_ids = list()
    is_delete = MaybeBool('is_delete')

    def __init__(self, *args, **kwargs) -> None:
        self.general_ids = kwargs.get('general_ids')
        self.is_delete = kwargs.get('isDelete')
        
        super().__init__(*args, **kwargs)

class GeneralVersionLog(ConfigMetaClass):
    general_id = MustInteger('general_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('general_id')
        
        super().__init__(*args, **kwargs)


class GeneralVersionLogAdd(ConfigMetaClass):
    general_id = MustInteger('general_id')
    version_id = MustInteger('version_id')
    name = MustString('name')
    status = MustString('status')
    info = MustString('info')
    user = MustString('user')
    update_time = MustDateTime('update_time')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('general_id')
        self.version_id = kwargs.get('version_id')
        self.name = kwargs.get('name')
        self.status = kwargs.get('status')
        self.info = kwargs.get('info')
        self.user = kwargs.get('user')
        self.update_time = kwargs.get('update_time')

        super().__init__(*args, **kwargs)


class GeneralRender(ConfigMetaClass):
    general_id = MustInteger('general_id')
    version_id = MustInteger('version_id')
    
    def __init__(self, *args, **kwargs) -> None:
        self.general_id = kwargs.get('id')
        self.version_id = kwargs.get('version_id')
        
        super().__init__(*args, **kwargs)
