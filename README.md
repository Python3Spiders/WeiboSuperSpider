# 作者简介


|作者|[inspurer](https://inspurer.github.io/2018/06/07/%E6%9C%88%E5%B0%8F%E6%B0%B4%E9%95%BF%E7%9A%84%E7%94%B1%E6%9D%A5/#more)|
|:---:|:---:|
|QQ交流群|[861016679](https://jq.qq.com/?_wv=1027&k=5Js6sKS)|
|个人博客|[https://inspurer.github.io/](https://inspurer.github.io/)|

项目详情请参考微信原文链接：[https://mp.weixin.qq.com/s/d_sJNbnOiEN2pCP2dZbYbw](https://mp.weixin.qq.com/s/d_sJNbnOiEN2pCP2dZbYbw)

如有疑问可通过公众号找到作者，微信扫描下方二维码或者在微信内搜索 **微信公众号：月小水长（ID:inspurer)**；

<p align="center">
  <img src="qrcode.jpg"></a>
</p>

# WeiboSuperScrapy
最强微博爬虫，用户、话题、评论一网打尽。

## GUI 功能集中版

运行 GUI.py 即可爬取用户/话题微博

运行 WeiboCommentScrapy.py 并修改里面的微博id (wid) 即可爬取指定微博的所有评论。

## 无 GUI 功能独立版

单独的 py 文件分别对立一个 功能

WeiboCommentScrapy.py 爬取评论

WeiboTopicScrapy.py   爬取指定关键词的所有微博，突破了 50 页的限制，可指定~截至日期~时间段搜索（比如 20200101-20200102）

WeiboSuperCommentScrapy.py 可爬取一条微博的所有评论，更为强大


## Reference

[https://www.jianshu.com/p/8dc04794e35f](https://www.jianshu.com/p/8dc04794e35f)
