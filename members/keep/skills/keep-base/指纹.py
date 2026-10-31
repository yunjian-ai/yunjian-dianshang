"""算官方页面正文指纹：去掉导航和页尾，只留「更新时间」到「这篇文章是否对你有帮助」之间的正文，压掉空白后取 sha256 前 12 位。
用法：python3 指纹.py <取回的正文.txt>      巡检.py 也用它；指纹变了就是正文改了。"""
import hashlib, re, sys

def zhengwen(t):
    k = t.find('----正文----')          # 取原文.mjs 存的正文文件：只认分隔线以后的正文
    if k >= 0:
        return re.sub(r'\s+', '', t[k + len('----正文----'):])
    i = t.find('更新时间')
    t = t[i:] if i >= 0 else t
    j = t.find('这篇文章是否对你有帮助')
    t = t[:j] if j >= 0 else t
    t = re.sub(r'阅读量[:：]\s*\d+', '', t)
    return re.sub(r'\s+', '', t)

def zhiwen(t):
    return hashlib.sha256(zhengwen(t).encode()).hexdigest()[:12]

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(zhiwen(open(p, encoding='utf-8').read()), p)
