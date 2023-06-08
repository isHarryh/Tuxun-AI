import os, math
import torchvision.transforms as transforms
from torchvision.datasets import VisionDataset
from PIL import Image
from io import BytesIO


class StreetViewDataset():
    '''Street View Dataset class'''

    def __init__(self, street_view_data:dict={}, targets:dict=None):
        self.data:dict = street_view_data
        '''The dictionary mapping each image's key(string) to its information.'''
        self.targets:dict = targets if targets else self.__get_targets()
        '''The dictionary mapping the number(string) of each target place to its information.'''

    def get_cleansed(self, keep_targets_topk:int, max_merging_distance:float=1000):
        '''
        Cleanse the dataset. \n
        The target places whose frequency is in the top-k will be kept.
        Other targets with low frequency will be merged into the nearest top-k,
        but if the distance is greater than the specified max merging distance, this target will be abandoned.
        :returns: The cleansed dataset object.
        '''
        new_data = self.data.copy()
        keeps = list(self.targets.items())
        keeps = sorted(keeps, key=lambda x: x[1]['frequency'], reverse=True)[:keep_targets_topk]
        keeps_name = [x[1]['name'] for x in keeps]

        for i in list(new_data.keys()):
            cur = new_data[i]
            if cur['target'] not in keeps_name:
                nears = keeps.copy()
                lng1, lat1 = cur['lng'], cur['lat']
                for j in nears:
                    lng2, lat2 = j[1]['lng'], j[1]['lat']
                    j[1]['distance'] = self.get_distance(lng1, lat1, lng2, lat2)
                nears = sorted(nears, key=lambda x: x[1]['distance'], reverse=False)[0]
                # print(f"{new_data[i]['target']} -> { nears[1]['name']} (d={round(nears[1]['distance'])}km)")
                if nears[1]['distance'] > max_merging_distance:
                    new_data.pop(i)
                else:
                    new_data[i]['target'] = nears[1]['name']

        return StreetViewDataset(new_data)

    @staticmethod
    def get_distance(lng1:float, lat1:float, lng2:float, lat2:float):
        def haversine(theta):
            h = math.sin(theta / 2)
            return h * h
        RADIUS = 6371

        lng1, lat1 = math.radians(lng1), math.radians(lat1)
        lng2, lat2 = math.radians(lng2), math.radians(lat2)
        dlng, dlat = math.fabs(lng1 - lng2), math.fabs(lat1 - lat2)
        hav = haversine(dlat) + math.cos(lat1) * math.cos(lat2) * haversine(dlng)
        return 2 * RADIUS * math.asin(math.sqrt(hav))

    def __get_targets(self):
        targets = {}
        for i in self.data.keys():
            tar = self.data[i]['target']
            if tar not in targets.keys():
                targets[tar] = [self.data[i]]
            else:
                targets[tar].append(self.data[i])
        total_places = len(self.data)
        total_targets = len(targets)

        result = {}
        for tar, i in zip(sorted(list(targets.keys())), range(total_targets)):
            avg_lng = sum([j['lng'] for j in targets[tar]]) / len(targets[tar])
            avg_lat = sum([j['lat'] for j in targets[tar]]) / len(targets[tar])
            frequency = len(targets[tar]) / total_places
            result[i] = {
                'name': tar,
                'lng': round(avg_lng, 5),
                'lat': round(avg_lat, 5),
                'frequency': round(frequency, 5)
            }
        return result


class StreetViewImageDataset(VisionDataset):
    '''Street View Image Dataset class'''

    enhance_methods = [
        lambda img: img.crop((0, 0, img.width // 2, img.height)) if img.width > img.height else img.crop((0, 0, img.height // 2, img.width)),
        lambda img: img.crop((img.width // 2, 0, img.width, img.height)) if img.width > img.height else img.crop((img.height // 2, 0, img.height, img.width))
    ]
    image_size = (224, 224)
    image_ext = '.jpg'
    transform = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __init__(self, root:str, street_view_dataset:StreetViewDataset, transform:transforms.Compose=transform):
        super(StreetViewImageDataset, self).__init__(root, transform=transform)
        self.data = street_view_dataset.data
        self.targets = street_view_dataset.targets
        self.classes = list(street_view_dataset.targets.keys())
        self.num_classes = len(self.classes)
        self.load_image_data()

    def __getitem__(self, index):
        object = list(self.data.values())[index % self.__real_len__()]
        binary = object['image']
        label = object['target']

        img = Image.open(BytesIO(binary))
        img = self.trim_image_bottom_blank(img)
        
        mode = len(self) % len(self.enhance_methods)
        img = self.enhance_methods[mode](img)
        img = self.transform(img)
        return img, self.target_to_index(label)

    def __len__(self):
        return self.__real_len__() * len(self.enhance_methods)
    
    def __real_len__(self):
        return len(self.data)
    
    def load_image_data(self):
        for i in list(self.data.keys()):
            try:
                fpath = os.path.join(self.root, i + self.image_ext)
                binary = open(fpath, 'rb').read()
                self.data[i]['image'] = binary
            except:
                self.data.pop(i)
    
    @staticmethod
    def trim_image_bottom_blank(img:Image.Image):
        _img = img.convert('L')
        width, height = img.width, img.height
        try:
            for y in range(0, height):
                y = height - y - 1
                if _img.getpixel((0, y)) > 0 and _img.getpixel((width - 1, y)) > 0:
                    return img.crop((0, 0, width, y - 1))
        except:
            pass
        return img
    
    def target_to_index(self, target):
        for i in range(len(self.targets)):
            if target == self.targets[i]['name']:
                return i
    
    def index_to_target(self, index):
        return self.targets[index]['name']
