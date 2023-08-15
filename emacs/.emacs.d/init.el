;; -*- lexical-binding: t -*-
(add-to-list 'load-path "~/.emacs.d/config/")


(require 'init-melpa)
(require 'init-ui)
(require 'init-package)
(require 'init-kbd)
(require 'init-lsp)
(require 'init-org)
(require 'init-hugo)
(require 'init-mode)
(require 'init-custom)
(require 'init-eaf)
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(c-hanging-braces-alist
   '((defun-open before after)
     (defun-close before after)
     (class-open before after)
     (class-close before after)
     (inline-open before after)
     (inline-close before after)
     (block-open before after)
     (block-close . c-snug-do-while)
     (statement-cont)
     (substatement-open after)
     (brace-list-open)
     (brace-entry-open)
     (extern-lang-open after)
     (namespace-open after)
     (module-open after)
     (composition-open after)
     (inexpr-class-open after)
     (inexpr-class-close before)
     (arglist-cont-nonempty)))
 '(elfeed-feeds
   '("https://rustcc.cn/rss" "https://www.codedump.info/index.xml" "https://blog.codinglabs.org/rss.xml" "https://www.archlinuxcn.org/feed/" "https://stardiviner.github.io/Blog/index.xml" "https://emacstalk.github.io/podcast/index.xml" "https://www.reddit.com/r/orgmode.rss" "https://hnrss.org/newest?q=emacs" "https://www.reddit.com/r/emacs.rss" "https://linux.cn/rss.xml" "http://feedmaker.kindle4rss.com/feeds/gh_10a6b96351a9.weixin.xml" "https://www.freebuf.com/feed" "http://blog.sina.com.cn/rss/1286528122.xml" "http://feedmaker.kindle4rss.com/feeds/cn.infoq.xml" "https://rsshub.app/juejin/category/article" "http://feedmaker.kindle4rss.com/feeds/almosthuman2014.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/jianshuio.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/banyuetan-weixin.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/youshucc.weixin.xml" "https://feedx.net/rss/shanghaishuping.xml" "http://blog.farmostwood.net/feed" "http://feedmaker.kindle4rss.com/feeds/hexun.com.xml" "https://coolshell.cn/feed" "http://www.mifengtd.cn/feed.xml" "https://rsshub.app/zhihu/hotlist" "https://linuxtoy.org/feeds/all.atom.xml" "http://feedmaker.kindle4rss.com/feeds/mydrivers.xml" "http://www.zhihu.com/rss" "http://feedmaker.kindle4rss.com/feeds/book_review_best.douban.xml" "http://feedmaker.kindle4rss.com/feeds/toutiao.io.xml" "https://feedex.net/feed/movie.douban.com/feed/review/movie" "http://feedmaker.kindle4rss.com/feeds/capitalnews.weixin.xml" "https://www.oschina.net/project/rss" "http://feedmaker.kindle4rss.com/feeds/luojisw.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/woshipm.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/duhaoshu.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/qiubai2005.weixin.xml" "http://www.joyloft.net/?feed=rss2" "http://www.google.com/reader/public/atom/user/09166964415516033892/state/com.google/broadcast"  "http://dev.oblog.cn/rss2.asp" "http://feed.feedsky.com/seoseo" "http://feed.feedsky.com/webleonsblog" "http://feed.feedsky.com/dwgoogle" "http://blog.donews.com/liuren/Rss.aspx" "http://www.ipang.net/feed/" "http://feed.zuola.com/" "http://www.duduwolf.com/rss.xml" "http://jiangzhanyong.com/feed" "http://robertmao.com/feed" "http://www.chinamyhosting.com/seoblog/feed/" "http://www.wespoke.com/index.rdf" "http://www.jingzhengli.cn/Blog/rss2.asp" "http://www.xucx.com/blog/rss.xml" "http://www.dunsh.org/feed/" "http://www.ufoer.com/rss.xml" "http://google.blogoscoped.cn/?feed=rss2" "http://www.chedong.com/blog/index.rdf" "http://blog.donews.com/tinyfool/Rss.aspx" "http://www.shunz.net/rssfeed" "http://maitian.blog.techweb.com.cn/rss2.xml" "http://misaiah.spaces.live.com/feed.rss" "http://buchimifan.yculblog.com/rss.xml" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1190363061" "http://www.luoyonghao.net/blogs/laoluo/Rss.aspx" "http://www.edu2do.com/fanyi/?feed=rss2" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1195403385" "http://mumu6.blog.sohu.com/rss" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1195201334" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1219548027" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1182391231" "http://www.1blog.cn/rss.xml" "http://feeds.feedburner.com/wangpei" "http://vivianlock.spaces.live.com/feed.rss" "http://blog.xoyo.com/rss.php?name=kingsoft" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1189729754" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1191258123" "http://googlechinablog.com/atom.xml" "http://sogou.blog.sohu.com/rss" "http://labs.blog.sohu.com/rss" "http://hi.baidu.com/baidu/rss" "http://www.googlechinawebmaster.com/feed/" "http://ysearchblog.cn/index.xml" "http://feeds.feedburner.com/my1510recommded" "http://feeds.feedburner.com/wangxiaofeng" "http://feeds.feedburner.com/china-week" "http://www.chinadialogue.cn/article/rss/ch" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1224623833" "http://www.daynew.net/?feed=rss2" "http://blog.sohu.com/members/zhaomu/rss" "http://www.bullog.cn/blogs/rosu/Rss.aspx" "http://blog.sohu.com/members/plum/rss" "http://www.playbeyond.cn/feed/" "http://www.ftchinese.com/sc/rss2_full.jsp" "http://www.aigaogao.com/blog/rss.aspx" "http://feeds.feedburner.com/BloggerBuzz" "http://googleajaxsearchapi.blogspot.com/atom.xml" "http://analytics.blogspot.com/atom.xml" "http://code.google.com/feeds/updates.xml" "http://googlemalwareblog.blogspot.com/atom.xml" "http://googlemapsapi.blogspot.com/atom.xml" "http://googleonlinesecurity.blogspot.com/atom.xml" "http://googlewebmastercentral.blogspot.com/atom.xml" "http://adsense.blogspot.com/atom.xml" "http://adwords.blogspot.com/atom.xml" "http://googledesktop.blogspot.com/atom.xml" "http://gmailblog.blogspot.com/atom.xml" "http://googleblog.blogspot.com/atom.xml" "http://googlereader.blogspot.com/atom.xml" "http://www.43folders.com/feed/" "http://blog.del.icio.us/blog/index.rdf" "http://blog.dreamhost.com/feed/" "http://www.dreamhoststatus.com/feed/" "http://blog.outer-court.com/rss.xml" "http://www.joelonsoftware.com/rss.xml" "http://www.mattcutts.com/blog/feed/" "http://radar.oreilly.com/feed" "http://www.readwriteweb.com/rss.xml" "http://www.searchengineblog.com/atom.xml" "http://www.ysearchblog.com/index.xml" "http://www.gearthblog.com/index.xml" "http://google-latlong.blogspot.com/atom.xml" "http://googlemapsmania.blogspot.com/atom.xml" "http://googlesightseeing.com/feed/" "http://feeds.ogleearth.com/ogleearth" "http://www.panoramio.com/blog/feed/" "http://blog.wired.com/games/rss.xml" "http://www.bloggingpro.com/feed/" "http://feeds.copyblogger.com/Copyblogger" "http://www.doshdosh.com/feed/" "http://www.micropersuasion.com/rss.xml" "http://www.problogger.net/feed/" "http://www.successful-blog.com/feed/"))
 '(org-agenda-files
   '("~/resource/dailyNotes/Note/Tools/Emacs/Emacs-note.org" "/home/stone/resource/dailyNotes/dailyRoutine/Star/resources.org" "/home/stone/resource/dailyNotes/todolist.org"))
 '(org-agenda-insert-diary-extract-time nil)
 '(package-selected-packages
   '(fzf rust-mode org-checklist rg ox-hugo baidu-translate backup-each-save org-roam-ui elfeed org-tempo leetcode keyfreq geiser-chez elfeed-web el-secretario-elfeed simple-httpd websocket inf-ruby htmlize org-roam-server w3m emmet-mode company-web vue-mode org-download yaml-mode typescript-mode youdao-dictionary company-lsp org-bullets org-bullet swiper-helm window-numbering neotree historian flx counsel-web all-the-icons))
 '(treemacs-show-hidden-files t))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
