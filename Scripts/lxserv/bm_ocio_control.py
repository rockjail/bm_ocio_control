# python
import lx  # type: ignore
import lxu.command  # type: ignore
import modo  # type: ignore
import lxifc  # type: ignore

svc_listen = lx.service.Listener()
svc_command = lx.service.Command()

sCMD_UPDATE_OCIO_PREFS = "bm.updateOCIOprefs"
sCMD_UPDATE_SCENE_OCIO = "bm.updateSceneOCIO"
sCMD_SWAP_SCENE_OCIO = "bm.swapSceneOCIO"
sCMD_SWAP_OCIO_PREFS = "bm.swapOCIOPrefs"

sCMD_PREF_OCIO = "pref.value colormanagement.default_ocio_config"
sCMD_PREF_8BIT = "pref.value colormanagement.8bit_default_colorspace"
sCMD_PREF_16BIT = "pref.value colormanagement.16bit_default_colorspace"
sCMD_PREF_FLOAT = "pref.value colormanagement.float_default_colorspace"
sCMD_PREF_NUM = "pref.value colormanagement.numeric_default_colorspace"
sCMD_PREF_VIEW = "pref.value colormanagement.view_default_colorspace"

tOCIO_PREFS = (
    sCMD_PREF_OCIO,
    sCMD_PREF_8BIT,
    sCMD_PREF_16BIT,
    sCMD_PREF_FLOAT,
    sCMD_PREF_NUM,
    sCMD_PREF_VIEW,
)


sOCIO_CHANNEL = "ocioConfig"
tOCIO_DEF_CHANNELS = (
    sOCIO_CHANNEL,
    "def8bitColorspace",
    "def16bitColorspace",
    "defFloatColorspace",
)


class CmdListener(lxifc.CmdSysListener, lxifc.SceneItemListener):
    def __init__(self):
        self.com_obj = lx.object.Unknown(self)
        svc_listen.AddListener(self.com_obj)
        self.armed = True
        self.pre_scene = None
        self.cache = dict()

    def __del__(self):
        svc_listen.RemoveListener(self.com_obj)

    def cmdsysevent_ExecutePre(self, cmd, type, isSandboxed, isPostCmd):
        if self.armed:
            cmd = lx.object.Command(cmd)
            cmd_name = cmd.Name()
            cmd_args = svc_command.ArgsAsString(cmd, False)
            if cmd_name in ("scene.open", "scene.set"):
                scene = lx.eval("scene.set ?")
                self.pre_scene = scene
            if cmd_name == "item.channel" and "scene$ocioConfig" in cmd_args:
                scene = modo.Scene()
                for ch in tOCIO_DEF_CHANNELS:
                    self.cache[ch] = scene.sceneItem.channel(ch).get()
                print(self.cache)
            if (
                cmd_name == "pref.value"
                and "colormanagement.default_ocio_config" in cmd_args
            ):
                for pref in tOCIO_PREFS:
                    self.cache[pref] = lx.eval("%s ?" % pref)
                print(self.cache)

    def cmdsysevent_ExecutePost(self, cmd, isSandboxed, isPostCmd):
        if self.armed:
            cmd = lx.object.Command(cmd)
            cmd_name = cmd.Name()
            cmd_args = svc_command.ArgsAsString(cmd, False)
            if cmd_name in ("scene.open", "scene.set"):
                scene = lx.eval("scene.set ?")
                if scene != self.pre_scene:
                    lx.eval("%s ask:true" % sCMD_UPDATE_OCIO_PREFS)
            if cmd_name == "item.channel" and "scene$ocioConfig" in cmd_args:
                cmd = sCMD_SWAP_SCENE_OCIO
                for ch in tOCIO_DEF_CHANNELS:
                    cmd += " %s:{%s}" % (ch, self.cache[ch])
                print(cmd)
                lx.eval(cmd)
            if (
                cmd_name == "pref.value"
                and "colormanagement.default_ocio_config" in cmd_args
            ):
                cmd = sCMD_SWAP_OCIO_PREFS
                for pref in tOCIO_PREFS:
                    print(pref)
                    pref_val = pref.split(" ")[1]
                    cmd += " %s:{%s}" % (pref_val, self.cache[pref])
                print(cmd)
                try:
                    self.armed = False
                    lx.eval(cmd)
                except:
                    print("error")
                finally:
                    self.armed = True


class cmd_UpdateOcioPrefs(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add("ask", lx.symbol.sTYPE_BOOLEAN)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        arg_ask = self.dyna_Bool(0, False)
        scene = modo.Scene()
        scene_ocio = scene.sceneItem.channel("ocioConfig").get()
        scene_8bit = scene.sceneItem.channel("def8bitColorspace").get()
        scene_16bit = scene.sceneItem.channel("def16bitColorspace").get()
        scene_float = scene.sceneItem.channel("defFloatColorspace").get()

        # ask user if the argument is set
        if arg_ask:
            pref_ocio = lx.eval("%s ?" % sCMD_PREF_OCIO)
            pref_8bit = lx.eval("%s ?" % sCMD_PREF_8BIT)
            pref_16bit = lx.eval("%s ?" % sCMD_PREF_16BIT)
            pref_float = lx.eval("%s ?" % sCMD_PREF_FLOAT)
            # pref_num = lx.eval("%s ?" % sCMD_PREF_NUM)
            # pref_view = lx.eval("%s ?" % sCMD_PREF_VIEW)
            if any(
                [
                    scene_ocio != pref_ocio,
                    scene_8bit != pref_8bit,
                    scene_16bit != pref_16bit,
                    scene_float != pref_float,
                ]
            ):
                ask = modo.dialogs.yesNo(
                    "OCIO config difference",
                    "OCIO config used in scene is different to preferences.\n \
Do you want to change preferences to match scene?",
                )
                # return early if user clicks no
                if ask == "no":
                    return

        lx.eval('%s "%s"' % (sCMD_PREF_OCIO, scene_ocio))
        lx.eval('%s "%s"' % (sCMD_PREF_8BIT, scene_8bit))
        lx.eval('%s "%s"' % (sCMD_PREF_16BIT, scene_16bit))
        lx.eval('%s "%s"' % (sCMD_PREF_FLOAT, scene_float))
        lx.eval('%s "%s"' % (sCMD_PREF_NUM, scene_8bit))
        # TODO: figure out better way to handle default view space
        # right now assuming people work with sRGB monitor and
        # that profile exists on all OCIO configs used
        lx.eval('%s "%s:sRGB"' % (sCMD_PREF_VIEW, scene_ocio))

    def cmd_Flags(self):
        return lx.symbol.fCMD_UI


class cmd_UpdateSceneOCIO(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)

    def basic_Execute(self, msg, flags):
        scene = modo.Scene()
        pref_ocio = lx.eval("%s ?" % sCMD_PREF_OCIO)
        pref_8bit = lx.eval("%s ?" % sCMD_PREF_8BIT)
        pref_16bit = lx.eval("%s ?" % sCMD_PREF_16BIT)
        pref_float = lx.eval("%s ?" % sCMD_PREF_FLOAT)

        scene.sceneItem.channel("ocioConfig").set(pref_ocio)
        scene.sceneItem.channel("def8bitColorspace").set(pref_8bit)
        scene.sceneItem.channel("def16bitColorspace").set(pref_16bit)
        scene.sceneItem.channel("defFloatColorspace").set(pref_float)

    def cmd_Flags(self):
        return lx.symbol.fCMD_UNDO


class cmd_SwapSceneOCIO(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        for ch in tOCIO_DEF_CHANNELS:
            self.dyna_Add(ch, lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        scene_ocio_old = self.dyna_String(self.attr_Lookup(sOCIO_CHANNEL), "")
        scene = modo.Scene()
        scene_ocio = scene.sceneItem.channel(sOCIO_CHANNEL).get()

        for ch in tOCIO_DEF_CHANNELS:
            val = self.dyna_String(self.attr_Lookup(ch), "")
            val = val.replace(scene_ocio_old, scene_ocio)
            scene.sceneItem.channel(ch).set(val)

    def cmd_Flags(self):
        return lx.symbol.fCMD_UNDO


class cmd_SwapOCIOPrefs(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        for pref in tOCIO_PREFS:
            pref = pref.split(" ")[1]
            self.dyna_Add(pref, lx.symbol.sTYPE_STRING)

    def basic_Execute(self, msg, flags):
        pref_ocio_old = self.dyna_String(
            self.attr_Lookup(sCMD_PREF_OCIO.split(" ")[1]), ""
        )
        pref_ocio = lx.eval("%s ?" % sCMD_PREF_OCIO)
        for pref in tOCIO_PREFS:
            pref_val = pref.split(" ")[1]
            val = self.dyna_String(self.attr_Lookup(pref_val), "")
            val = val.replace(pref_ocio_old, pref_ocio)
            lx.eval("%s {%s}" % (pref, val))

    def cmd_Flags(self):
        return lx.symbol.fCMD_UNDO


lx.bless(cmd_UpdateOcioPrefs, sCMD_UPDATE_OCIO_PREFS)
lx.bless(cmd_UpdateSceneOCIO, sCMD_UPDATE_SCENE_OCIO)
lx.bless(cmd_SwapSceneOCIO, sCMD_SWAP_SCENE_OCIO)
lx.bless(cmd_SwapOCIOPrefs, sCMD_SWAP_OCIO_PREFS)

cmdListener1 = CmdListener()
