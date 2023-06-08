import os, json
import torch
from Dataset import *
from Model import *
from TuxunAgent import *


if __name__ == '__main__':
    # 凭据验证
    os.chdir(os.path.dirname(__file__))
    cookie_path = "cookie.txt"
    if not os.path.isfile(cookie_path):
        open(cookie_path, 'x').close()
    
    agent = TuxunAgent()
    cookie = open(cookie_path, 'r').read().replace('\n', '').replace('\r', '')
    agent.set_cookie(cookie)
    uid = agent.get_user_id()
    if type(uid) != str:
        print("无法登录图寻。可能未设置有效的用户凭据 Cookie 或无法访问图寻服务器。")
        print("  请参考说明文档进行凭据配置：https://github.com/isHarryh/Tuxun-AI#readme")
        print(uid)
        input()
        exit()
    print(f"当前用户：UID {uid}")

    # 载入模型
    print("正在加载模型...")
    mapping_path = os.path.join("models", "mapping.json")
    model_path = os.path.join("models", "v0.3.0.pth")
    mapping = json.load(open(mapping_path, 'r', encoding='UTF-8'))
    model = TuxunAIModelV0(classifier=TuxunAIModelV0.get_classifier(len(mapping)))
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model = model.to('cpu')
    model.eval()

    while True:
        try:
            # 获得题目信息
            print("")
            gid = input("请输入图寻 GameID: ")
            game = agent.get(gid)
            if type(game) != TuxunGame:
                print("错误：获取对局失败")
                print(game)
                continue
            print(f"★ Round {len(game.rounds)}")

            # 下载街景
            print("  正在获取街景图片...")
            sv = StreetView(game.pano)
            if type(sv.get_type()) == StreetViewException:
                print("  错误：不支持的街景类型")
                continue

            img = sv.get_image()
            try:
                img = img.convert('RGB')
            except:
                print("  错误：获取街景失败")
                print(img)
                continue

            # 输入模型
            print("  正在分析...")
            outputs = None
            for method in StreetViewImageDataset.enhance_methods:
                image = img.copy()
                image = StreetViewImageDataset.trim_image_bottom_blank(image)
                image = method(image)
                image = StreetViewImageDataset.transform(image)
                image = torch.autograd.Variable(image, requires_grad=True)
                image = image.unsqueeze(0)
                outputs = outputs + model(image) if outputs != None else model(image)

            k = 5
            topk_predicted = torch.topk(outputs.data, k=k, dim=1)[1].numpy().tolist()[0]
            confs = torch.nn.functional.softmax(outputs, dim=1).detach().numpy().tolist()[0]

            for idx, top in zip(topk_predicted, range(k)):
                target = mapping[str(idx)]
                conf = round(confs[idx] * 100)
                # 输出预测
                conf_str= "<1%" if conf < 1 else f"{conf}%"
                print(f"  TOP {top+1}: {target['name']}\t置信 {conf_str}\t经纬 ({round(target['lng'])}°,{round(target['lat'])}°)")

        except Exception as arg:
            print(f"错误：{arg}")
