# T1 Q2 生成器分页加载器（挂项目 1.1）
# 撞墙记录：
#   墙1：第一版我把残余页逻辑写在 for 循环内部，最后一页丢数据，跑出来页数不对才反应过来
#        残余页要在 source 耗尽后（循环外）再 yield 一次。
#   墙2：想「再打印一遍所有页」做校验，第二次遍历一页都没有——当场愣住，
#        这就是题干要的「第二次消费为空」，顺手把它变成了演示段。

def paged_loader(source, page_size):
    """生成器：从 source 逐项取数，攒满 page_size 就 yield 一页。"""
    page = []
    for item in source:
        page.append(item)
        if len(page) >= page_size:
            yield page
            page = []
    if page:            # 残余页：source 耗尽时不足一页的部分
        yield page


# 百万级数据源用生成器表达式模拟，全程不物化成 list
big_source = (i for i in range(1_000_000))

pages = paged_loader(big_source, 300_000)
total_items = 0
for i, page in enumerate(pages):
    total_items += len(page)
    print(f"第{i+1}页: 长度={len(page)}, 首={page[0]}, 尾={page[-1]}")
print("总条数:", total_items)

print("\n=== 演示：同一个生成器第二次消费为空 ===")
small_source = (i for i in range(5))
loader = paged_loader(small_source, 2)
print("第一次消费:", list(loader))   # [[0,1],[2,3],[4]]
print("第二次消费:", list(loader))   # [] —— 生成器对象本身就是迭代器，
# 状态（挂起的执行帧）在第一次消费完就 Exhausted 了，
# iter(loader) 返回的还是它自己，没有新状态可给，直接 StopIteration。
# Swift 类比：Sequence 可以反复 makeIterator()，这里相当于 Sequence 和 Iterator 是同一个对象。
