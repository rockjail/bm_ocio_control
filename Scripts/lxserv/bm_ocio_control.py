# python
import lx  # type: ignore
import lxu.command  # type: ignore
import modo  # type: ignore
import lxifc  # type: ignore

svc_listen = lx.service.Listener()
svc_commnad = lx.service.Command()

sCMD_UPDATE_OCIO_PREFS = "bm.updateOCIOprefs"

sCMD_PREF_OCIO = "pref.value colormanagement.default_ocio_config"
sCMD_PREF_8BIT = "pref.value colormanagement.8bit_default_colorspace"
sCMD_PREF_16BIT = "pref.value colormanagement.16bit_default_colorspace"
sCMD_PREF_FLOAT = "pref.value colormanagement.float_default_colorspace"
sCMD_PREF_NUM = "pref.value colormanagement.numeric_default_colorspace"
sCMD_PREF_VIEW = "pref.value colormanagement.view_default_colorspace"


class CmdListener(lxifc.CmdSysListener, lxifc.SceneItemListener):
    def __init__(self):
        self.com_obj = lx.object.Unknown(self)
        svc_listen.AddListener(self.com_obj)
        self.armed = True

    def __del__(self):
        svc_listen.RemoveListener(self.com_obj)

    def cmdsysevent_ExecutePost(self, cmd, isSandboxed, isPostCmd):
        if self.armed:
            cmd = lx.object.Command(cmd)
            if cmd.Name() in ("scene.open", "scene.set"):
                lx.eval(f"{sCMD_UPDATE_OCIO_PREFS} ask:true")


class cmd_UpdateOcioPrefs(lxu.command.BasicCommand):

    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('ask', lx.symbol.sTYPE_BOOLEAN)
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
            pref_ocio = lx.eval(f"{sCMD_PREF_OCIO} ?")
            pref_8bit = lx.eval(f"{sCMD_PREF_8BIT} ?")
            pref_16bit = lx.eval(f"{sCMD_PREF_16BIT} ?")
            pref_float = lx.eval(f"{sCMD_PREF_FLOAT} ?")
            # pref_num = lx.eval(f"{sCMD_PREF_NUM} ?")
            # pref_view = lx.eval(f"{sCMD_PREF_VIEW} ?")
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
        
        lx.eval(f'{sCMD_PREF_OCIO} "{scene_ocio}"')
        lx.eval(f'{sCMD_PREF_8BIT} "{scene_8bit}"')
        lx.eval(f'{sCMD_PREF_16BIT} "{scene_16bit}"')
        lx.eval(f'{sCMD_PREF_FLOAT} "{scene_float}"')
        lx.eval(f'{sCMD_PREF_NUM} "{scene_8bit}"')
        # TODO: figure out better way to handle default view space
        # right now assuming people work with sRGB monitor and that profile exists on all OCIO configs used
        lx.eval(f'{sCMD_PREF_VIEW} "{scene_ocio}:sRGB"')

    def cmd_Flags(self):
        return lx.symbol.fCMD_UI


lx.bless(cmd_UpdateOcioPrefs, sCMD_UPDATE_OCIO_PREFS)

cmdListener1 = CmdListener()