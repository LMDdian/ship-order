import argparse
from datetime import timedelta

import os
import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2.types import Credentials, CredentialsProvider

class DjangoEnvCredentialsProvider(CredentialsProvider):
    """从Django的settings（读取自.env）中获取OSS凭证"""

    def __init__(self) -> None:
        # 从Django settings中读取，替代os.getenv
        access_key_id = os.getenv("OSS_ACCESS_KEY_ID") or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET") or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        session_token = None

        # # 校验必填项：ID或Secret为空则抛异常
        # if not access_key_id or not access_key_secret:
        #     raise CredentialsEmptyError(
        #         "请在Django的.env文件中配置OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET"
        #     )
        if not access_key_id or not access_key_secret:
            raise ValueError(
                "缺少 OSS 凭证：请在环境变量中配置 OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET "
                "（或 ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET）。"
            )

        # 封装成凭证对象
        self._credentials = Credentials(access_key_id, access_key_secret, session_token)

    def get_credentials(self) -> Credentials:
        """对外提供凭证对象（SDK会调用这个方法）"""
        return self._credentials

def main():
    # 从环境变量中加载访问OSS所需的认证信息，用于身份验证
    credentials_provider = DjangoEnvCredentialsProvider()

    # 使用SDK的默认配置创建配置对象，并设置认证提供者
    cfg = oss.config.load_default()
    cfg.credentials_provider = credentials_provider
    
    # 设置配置对象的区域属性，根据用户提供的命令行参数
    cfg.region = 'cn-hangzhou'

    # # 如果提供了自定义endpoint，则更新配置对象中的endpoint属性
    # if args.endpoint is not None:
    #     cfg.endpoint = args.endpoint

    # 使用上述配置初始化OSS客户端，准备与OSS交互
    client = oss.Client(cfg)


    # 生成预签名的 PUT 上传请求（与前端 ImageUpload 直传 OSS 配套）
    urls = []
    for i in range(5):
        result = client.presign(
            oss.PutObjectRequest(
                bucket='i-bp1jb3693mcv9bh9wuhz2',
                key=f'images/2026/02/ceshi_{i}.png',
                content_type="application/octet-stream",
            ),
            expires=timedelta(minutes=15),
        )
        urls.append(result.url)
    print(urls)

    # 打印操作结果的各种元数据信息



# 当此脚本被直接执行时，调用main函数开始处理逻辑
if __name__ == "__main__":
    main()  # 脚本入口点，控制程序流程从这里开始