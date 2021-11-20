import os
from math import radians

from flask import Blueprint, render_template, request

from file_config.parts import backpacks, heads, arms, bodies, hands, legs, designers
from forms.make import GenerateMini, MissingFiles
from utils.dict import deep_get
from utils.mesh import connect_mesh
from utils.thingiverse import download_object

make_bp = Blueprint('make_bp', __name__)


@make_bp.route('/', methods=['GET', 'POST'])
def make_nameplate():
    form = GenerateMini()
    print(request.remote_addr)
    if request.method == 'POST':
        results = request.form.to_dict()
        # print(results)
        form.backpack.choices = list(zip(backpacks[results.get('backpack_')]['stl'],
                                         backpacks[results.get('backpack_')]['stl']))
        form.head.choices = list(zip(heads[results.get('head_')]['stl'],
                                     heads[results.get('head_')]['stl']))
        form.rarm.choices = list(zip(arms[results.get('rarm_')]['stl'],
                                     arms[results.get('rarm_')]['stl']))
        form.larm.choices = list(zip(arms[results.get('larm_')]['stl'],
                                     arms[results.get('larm_')]['stl']))
        form.body.choices = list(zip(bodies[results.get('body_')]['stl'],
                                     bodies[results.get('body_')]['stl']))
        form.rhand.choices = list(zip(hands[results.get('rhand_')]['stl'],
                                      hands[results.get('rhand_')]['stl']))
        form.lhand.choices = list(zip(hands[results.get('lhand_')]['stl'],
                                      hands[results.get('lhand_')]['stl']))
        form.leg.choices = list(zip(legs[results.get('leg_')]['stl'],
                                    legs[results.get('leg_')]['stl']))

        if "submit_preview" in results:
            print(results)
            left_hand = deep_get(hands, f"{results.get('lhand_')}|stl|{results.get('lhand')}")
            right_hand = deep_get(hands, f"{results.get('rhand_')}|stl|{results.get('rhand')}")
            head = deep_get(heads, f"{results.get('head_')}|stl|{results.get('head')}")
            body = deep_get(bodies, f"{results.get('body_')}|stl|{results.get('body')}")
            right_arm = deep_get(arms, f"{results.get('rarm_')}|stl|{results.get('rarm')}")
            left_arm = deep_get(arms, f"{results.get('larm_')}|stl|{results.get('larm')}")
            leg = deep_get(legs, f"{results.get('leg_')}|stl|{results.get('leg')}")
            backpack = deep_get(backpacks, f"{results.get('backpack_')}|stl|{results.get('backpack')}")

            lhand_path = deep_get(hands, f"{results.get('lhand_')}|desc|path")
            rhand_path = deep_get(hands, f"{results.get('rhand_')}|desc|path")
            head_path = deep_get(heads, f"{results.get('head_')}|desc|path")
            body_path = deep_get(bodies, f"{results.get('body_')}|desc|path")
            rarm_path = deep_get(arms, f"{results.get('rarm_')}|desc|path")
            larm_path = deep_get(arms, f"{results.get('larm_')}|desc|path")
            leg_path = deep_get(legs, f"{results.get('leg_')}|desc|path")
            backpack_path = deep_get(backpacks, f"{results.get('backpack_')}|desc|path")

            import trimesh as tm

            mleft_hand_path = {"path": f"{lhand_path}{left_hand['file']}", "info": left_hand}
            mright_hand_path = {"path": f"{rhand_path}{right_hand['file']}", "info": right_hand}
            mhead_path = {"path": f"{head_path}{head['file']}", "info": head}
            mbody_path = {"path": f"{body_path}{body['file']}", "info": body}
            mright_arm_path = {"path": f"{rarm_path}{right_arm['file']}", "info": right_arm}
            mleft_arm_path = {"path": f"{larm_path}{left_arm['file']}", "info": left_arm}
            mleg_path = {"path": f"{leg_path}{leg['file']}", "info": leg}
            mbackpack_path = {"path": f"{backpack_path}{backpack['file']}", "info": backpack}

            li_to_dl = []
            for path_info in [mleft_hand_path, mright_hand_path, mhead_path, mbody_path, mright_arm_path, mleft_arm_path, mleg_path, mbackpack_path]:
                if not os.path.isfile(path_info.get('path')):
                    print(f"{path_info.get('path')} is missing")
                    li_to_dl.append((path_info))

            if li_to_dl and results.get('download_missing_file'):
                for to_dl in li_to_dl:
                    if "thingiverse" in to_dl.get('info'):
                        download_object(to_dl.get('info').get('thingiverse'), to_dl.get('path'))
            elif li_to_dl:
                print("Check Download missing file !")
                return render_template('minicreator.html', form=form, designers={})

            mleft_hand = tm.load(mleft_hand_path.get('path'))
            mright_hand = tm.load(mright_hand_path.get('path'))
            mhead = tm.load(mhead_path.get('path'))
            mbody = tm.load(mbody_path.get('path'))
            mright_arm = tm.load(mright_arm_path.get('path'))
            mleft_arm = tm.load(mleft_arm_path.get('path'))
            mleg = tm.load(mleg_path.get('path'))
            mbackpack = tm.load(mbackpack_path.get('path'))

            connect_mesh(mhead, mbody, head, body, on='head', rotate=0, coef_merge=-0.3)
            connect_mesh(mleft_arm, mbody, left_arm, body, on='arm', dextral='left',
                         rotate=int(results.get('larm_rotation')), coef_merge=0)
            connect_mesh(mright_arm, mbody, right_arm, body, on='arm', dextral='right',
                         rotate=int(results.get('rarm_rotation')), coef_merge=0)
            connect_mesh(mleft_hand, mleft_arm, left_hand, left_arm, on='hand', dextral='left',
                         rotate=int(results.get('lhand_rotation')), coef_merge=0)
            connect_mesh(mright_hand, mright_arm, right_hand, right_arm, on='hand', dextral='right',
                         rotate=int(results.get('rhand_rotation')),
                         coef_merge=0)
            connect_mesh(mleg, mbody, leg, body, on='leg', rotate=0, coef_merge=0)
            connect_mesh(mbackpack, mbody, backpack, body, on='backpack', rotate=0, coef_merge=0)

            scene = (mhead + mbody + mleft_arm + mright_arm + mleft_hand + mright_hand + mleg + mbackpack)
            scene.apply_transform(tm.transformations.euler_matrix(radians(-90), 0, 0))

            from trimesh.viewer import scene_to_html

            todo_designer = {
                "name": "designer will be added soon",
                "donation": "TODO",
                "web": {
                }
            }

            designer = {
                "Designer of left_hand": designers.get(left_hand.get('designer', 'Nop'), todo_designer),
                "Designer of right_hand": designers.get(right_hand.get('designer', 'Nop'), todo_designer),
                "Designer of head": designers.get(head.get('designer', 'Nop'), todo_designer),
                "Designer of body": designers.get(body.get('designer', 'Nop'), todo_designer),
                "Designer of right_arm": designers.get(right_arm.get('designer', 'Nop'), todo_designer),
                "Designer of left_arm": designers.get(left_arm.get('designer', 'Nop'), todo_designer),
                "Designer of leg": designers.get(leg.get('designer', 'Nop'), todo_designer),
                "Designer of backpack": designers.get(backpack.get('designer', 'Nop'), todo_designer),
            }
            return render_template('minicreator.html', form=form, test=scene_to_html(scene.scene()),
                                   designers=designer)

    return render_template('minicreator.html', form=form, designers={})