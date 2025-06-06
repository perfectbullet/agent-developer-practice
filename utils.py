from os.path import abspath, dirname, join
def save_graph_image(graph, image_name):
    # 生成可视化图像结构
    img_data = graph.get_graph().draw_mermaid_png()
    image_path = join('graph_images', image_name + '.png')
    # 保存图像到文件
    with open(image_path, "wb") as f:
        res = f.write(img_data)
    return abspath(image_path)
