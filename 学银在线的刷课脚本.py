import asyncio
from pathlib import Path
from loguru import logger
from playwright.async_api import async_playwright

#用参数指定从第几个二级标题开始刷课，默认从第0个开始
async def main(argv:int = 0):
    async with async_playwright() as p:
        state_file = Path.home() / ".classScropt-playwright-state.json"
        browser = await p.chromium.launch(headless=False)
        if state_file.exists():
            context = await browser.new_context(storage_state=str(state_file))
        else:
            context = await browser.new_context()
        page = await context.new_page()
        #携带token进入网页
        await page.goto(
            "https://mooc1.xueyinonline.com/mycourse/studentstudy?chapterId=1246926895&courseId=267162735&clazzid=154883231&cpi=493348387&enc=8e78d6e002d00c52433a466349e22151&mooc2=1&hidetype=0&fanyaVersion=0&openc=774cae0db541c508a7b3ed836cfb7c44"
        )
        #先把所有二级标题找出来
        items = page.locator(".posCatalog_name")
        for i in range(argv,await items.count()):
            item = items.nth(i)
            title = await item.get_attribute("title")
            await item.click()
            logger.info(f"当前在{title}下")
            await asyncio.sleep(5)
            #进入该二级标题再找视频元素
            #这个网页的视频元素在iframe中，所以要遍历所有的frame去找播放按钮
            logger.info(f"开始查找视频元素")
            button_has:bool=False
            for index, frame in enumerate(page.frames):
                count = await frame.locator("button.vjs-big-play-button").count()
                logger.info(
                    f"frame[{index}]，名称={frame.name!r}，播放按钮数量={count}"
                )
                if count > 0:
                    logger.info(f"在frame[{index}]中找到了播放按钮")
                    button_has = True
                    await frame.locator("button.vjs-big-play-button").click()
                    break
            if not button_has:
                logger.warning(f"没有找到播放按钮，跳过该二级标题")
                continue
            logger.info(f"开始播放视频")
            video = frame.locator("video")
            was_paused = False
            # 每两秒检查实际播放状态，暂停或缓冲时继续等待当前视频
            while True:
                state = await video.evaluate(
                    "video => ({ended: video.ended, paused: video.paused})"
                )
                if state["ended"]:
                    logger.info("视频播放完毕，进入下一节")
                    break
                if state["paused"] and not was_paused:
                    logger.warning("视频已暂停，请检查页面并处理；恢复播放后将继续等待")
                elif was_paused and not state["paused"]:
                    logger.info("视频已恢复播放")
                was_paused = state["paused"]
                await asyncio.sleep(2)


        input()
        await context.storage_state(path=str(state_file))
        await context.close()
        await browser.close()


asyncio.run(main(argv=4))
