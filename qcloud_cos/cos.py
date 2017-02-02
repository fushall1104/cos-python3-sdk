from httplib2 import Http
import random
import time
import urllib
import hmac
import hashlib
import binascii
import base64



class Cos:
    def __init__(self, app_id, secret_id, secket_key, region="shanghai"):
        self.config = CosConfig()
        self.config.app_id = app_id
        self.config.secret_id = secret_id
        self.config.secret_key = secket_key
        self.config.region = region

    def get_bucket(self, bucket_name):
        return CosBucket(self.config, bucket_name)

class CosConfig:
    app_id = 0
    secret_id = ''
    secret_key = ''
    region = ''
    bucket = ''
class CosBucket:

    """初始化操作"""
    def __init__(self, cos_config, bucket_name):
        self.config = cos_config
        self.config.bucket = bucket_name
        self.http = Http()
        self.headers = {'Content-Type': 'application/json'}

    """创建目录"""
    def create_folder(self, dir_name):
        self.url = "<Region>.file.myqcloud.com" + "/files/v2/<appid>/<bucket_name>/<dir_name>/"
        self.url = process_url(self.url, self.config)
        self.url = str(self.url).replace("<bucket_name>", self.config.bucket).replace("<dir_name>",dir_name)
        self.url = 'http://' + self.url
        self.headers['Authorization'] = CosAuth(self.config).sign_more(self.config.bucket, '', 30 )
        response,content = self.http.request(uri=self.url, method='POST', body='{"op": "create", "biz_attr": ""}', headers=self.headers)
        print(response)
        print(content)
"""处理url"""
def process_url(url, config):
    url = str(url)
    url = url.replace("<Region>",config.region).replace("<appid>", str(config.app_id))
    return url


class CosAuth(object):
    def __init__(self, config):
        self.config = config

    def app_sign(self, bucket, cos_path, expired, upload_sign=True):
        appid = self.config.app_id
        bucket = bucket
        secret_id = self.config.secret_id
        now = int(time.time())
        rdm = random.randint(0, 999999999)
        cos_path = urllib.parse.quote(cos_path.encode('utf8'), '~/')
        if upload_sign:
            fileid = '/%s/%s%s' % (appid, bucket, cos_path)
        else:
            fileid = cos_path

        if expired != 0 and expired < now:
            expired = now + expired

        sign_tuple = (appid, secret_id, expired, now, rdm, fileid, bucket)

        plain_text = 'a=%s&k=%s&e=%d&t=%d&r=%d&f=%s&b=%s' % sign_tuple
        secret_key = self.config.secret_key.encode('utf8')
        sha1_hmac = hmac.new(secret_key, plain_text.encode("utf8"), hashlib.sha1)
        hmac_digest = sha1_hmac.hexdigest()
        hmac_digest = binascii.unhexlify(hmac_digest)
        sign_hex = hmac_digest + plain_text.encode('utf8')
        sign_base64 = base64.b64encode(sign_hex)
        return sign_base64.decode('utf8')

    def sign_once(self, bucket, cos_path):
        """单次签名(针对删除和更新操作)

        :param bucket: bucket名称
        :param cos_path: 要操作的cos路径, 以'/'开始
        :return: 签名字符串
        """
        return self.app_sign(bucket, cos_path, 0)

    def sign_more(self, bucket, cos_path, expired):
        """多次签名(针对上传文件，创建目录, 获取文件目录属性, 拉取目录列表)

        :param bucket: bucket名称
        :param cos_path: 要操作的cos路径, 以'/'开始
        :param expired: 签名过期时间, UNIX时间戳, 如想让签名在30秒后过期, 即可将expired设成当前时间加上30秒
        :return: 签名字符串
        """
        return self.app_sign(bucket, cos_path, expired)

    def sign_download(self, bucket, cos_path, expired):
        """下载签名(用于获取后拼接成下载链接，下载私有bucket的文件)

        :param bucket: bucket名称
        :param cos_path: 要下载的cos文件路径, 以'/'开始
        :param expired:  签名过期时间, UNIX时间戳, 如想让签名在30秒后过期, 即可将expired设成当前时间加上30秒
        :return: 签名字符串
        """
        return self.app_sign(bucket, cos_path, expired, False)