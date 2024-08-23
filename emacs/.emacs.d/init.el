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
;; (require 'init-eaf)
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
   '("https://blog.cleancoder.com/atom.xml" "https://feeds.feedburner.com/2ality" "https://www.codedump.info/index.xml" "https://blog.codinglabs.org/rss.xml" "https://www.archlinuxcn.org/feed/" "https://stardiviner.github.io/Blog/index.xml" "https://emacstalk.github.io/podcast/index.xml" "https://www.reddit.com/r/orgmode.rss" "https://hnrss.org/newest?q=emacs" "https://www.reddit.com/r/emacs.rss" "https://linux.cn/rss.xml" "http://feedmaker.kindle4rss.com/feeds/gh_10a6b96351a9.weixin.xml" "https://www.freebuf.com/feed" "http://blog.sina.com.cn/rss/1286528122.xml" "http://feedmaker.kindle4rss.com/feeds/cn.infoq.xml" "https://rsshub.app/juejin/category/article" "http://feedmaker.kindle4rss.com/feeds/almosthuman2014.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/jianshuio.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/banyuetan-weixin.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/youshucc.weixin.xml" "https://feedx.net/rss/shanghaishuping.xml" "http://blog.farmostwood.net/feed" "http://feedmaker.kindle4rss.com/feeds/hexun.com.xml" "https://rss.lilydjwg.me/zhihuzhuanlan/c_1029672383375949824" "http://thehackernews.com/feeds/posts/default" "https://coolshell.cn/feed" "http://www.mifengtd.cn/feed.xml" "https://rsshub.app/zhihu/hotlist" "https://linuxtoy.org/feeds/all.atom.xml" "http://feeds.feedburner.com/zhihu-daily" "http://feedmaker.kindle4rss.com/feeds/mydrivers.xml" "http://www.zhihu.com/rss" "http://feedmaker.kindle4rss.com/feeds/book_review_best.douban.xml" "http://feedmaker.kindle4rss.com/feeds/toutiao.io.xml" "https://feedex.net/feed/movie.douban.com/feed/review/movie" "http://feedmaker.kindle4rss.com/feeds/capitalnews.weixin.xml" "https://www.oschina.net/project/rss" "http://feedmaker.kindle4rss.com/feeds/luojisw.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/woshipm.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/duhaoshu.weixin.xml" "http://feedmaker.kindle4rss.com/feeds/qiubai2005.weixin.xml" "http://feeds.feedburner.com/adsense-tw" "http://feeds.feedburner.com/angel-lived" "http://feeds.feedburner.com/athere" "http://feeds.feedburner.com/cathayan" "http://feeds.feedburner.com/blogbeta/chn" "http://feeds.feedburner.com/dbanotes" "http://feeds.feedburner.com/hhalloyy" "http://feeds.feedburner.com/Gfans" "http://feeds.feedburner.com/gg" "http://feeds.feedburner.com/moon-blog" "http://feeds.feedburner.com/HerockPost" "http://feed.feedsky.com/cutescr" "http://feed.feedsky.com/joychanblog" "http://feeds.feedburner.com/iwfwcf" "http://www.joyloft.net/?feed=rss2" "http://feeds.feedburner.com/kaku" "http://feed.feedsky.com/keepwalking" "http://www.google.com/reader/public/atom/user/09166964415516033892/state/com.google/broadcast" "http://feeds.feedburner.com/nicky" "http://feeds.feedburner.com/nings" "http://dev.oblog.cn/rss2.asp" "http://feeds.feedburner.com/PoseShow" "http://feeds.feedburner.com/SeoVista" "http://feeds.feedburner.com/seocn" "http://feed.feedsky.com/seoseo" "http://feeds.feedburner.com/sxuzone" "http://feeds.feedburner.com/TheSkyOfDaemon" "http://feeds.feedburner.com/Web2Week" "http://feed.feedsky.com/webleonsblog" "http://feeds.feedburner.com/kojichangeworld" "http://feed.feedsky.com/dwgoogle" "http://blog.donews.com/liuren/Rss.aspx" "http://feeds.feedburner.com/qianblogger" "http://www.ipang.net/feed/" "http://feeds.feedburner.com/blogsdiy" "http://feeds.feedburner.com/keneng" "http://www.feedsky.com/feed/lvxinxin" "http://feeds.feedburner.com/wuzhiyong" "http://feed.zuola.com/" "http://www.duduwolf.com/rss.xml" "http://feeds.feedburner.com/kunshou" "http://feeds.feedburner.com/comgeo" "http://feeds.feedburner.com/watsonxu1" "http://feeds.feedburner.com/Diglog" "http://feeds.feedburner.com/solidot" "http://feeds.feedburner.com/PlayinWithIt" "http://feeds.feedburner.com/guigui" "http://jiangzhanyong.com/feed" "http://robertmao.com/feed" "http://www.chinamyhosting.com/seoblog/feed/" "http://feed.feedsky.com/eryi" "http://www.wespoke.com/index.rdf" "http://www.jingzhengli.cn/Blog/rss2.asp" "http://www.xucx.com/blog/rss.xml" "http://feeds.feedburner.com/ilmay" "http://feed.feedsky.com/caozenghui" "http://feeds.feedburner.com/williamlong" "http://feeds.feedburner.com/moon-soft" "http://feeds.feedburner.com/moon-weblog" "http://feed.feedsky.com/zwblogger" "http://feeds.feedburner.com/Incomplete" "http://feeds.feedburner.com/mulberry" "http://feeds.feedburner.com/awflasher" "http://feeds.feedburner.com/calon" "http://www.dunsh.org/feed/" "http://feeds.feedburner.com/jandan" "http://www.ufoer.com/rss.xml" "http://feeds.feedburner.com/whitecrow" "http://feeds.feedburner.com/snowyowls" "http://feeds.feedburner.com/thwsblog" "http://feeds.feedburner.com/laobaisBlog" "http://feeds.feedburner.com/istef" "http://feed.feedsky.com/zhanbin" "http://feeds.feedburner.com/yeeyan_tech_zh" "http://google.blogoscoped.cn/?feed=rss2" "http://www.chedong.com/blog/index.rdf" "http://feeds.feedburner.com/googleview" "http://blog.donews.com/tinyfool/Rss.aspx" "http://feeds.feedburner.com/kuju" "http://feeds.feedburner.com/virushuo" "http://www.shunz.net/rssfeed" "http://feeds.feedburner.com/dragon4" "http://feeds.feedburner.com/flypigorg" "http://maitian.blog.techweb.com.cn/rss2.xml" "http://misaiah.spaces.live.com/feed.rss" "http://buchimifan.yculblog.com/rss.xml" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1190363061" "http://www.luoyonghao.net/blogs/laoluo/Rss.aspx" "http://www.edu2do.com/fanyi/?feed=rss2" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1195403385" "http://mumu6.blog.sohu.com/rss" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1195201334" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1219548027" "http://feeds.feedburner.com/caitou" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1182391231" "http://www.1blog.cn/rss.xml" "http://feeds.feedburner.com/wangpei" "http://vivianlock.spaces.live.com/feed.rss" "http://blog.xoyo.com/rss.php?name=kingsoft" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1189729754" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1191258123" "http://googlechinablog.com/atom.xml" "http://sogou.blog.sohu.com/rss" "http://labs.blog.sohu.com/rss" "http://hi.baidu.com/baidu/rss" "http://www.googlechinawebmaster.com/feed/" "http://ysearchblog.cn/index.xml" "http://feeds.feedburner.com/my1510recommded" "http://feeds.feedburner.com/wangxiaofeng" "http://feeds.feedburner.com/china-week" "http://www.chinadialogue.cn/article/rss/ch" "http://blog.sina.com.cn/myblog/index_rss.php?uid=1224623833" "http://www.daynew.net/?feed=rss2" "http://feeds.feedburner.com/mindm" "http://blog.sohu.com/members/zhaomu/rss" "http://www.bullog.cn/blogs/rosu/Rss.aspx" "http://feeds.feedburner.com/xiangge" "http://blog.sohu.com/members/plum/rss" "http://www.playbeyond.cn/feed/" "http://feeds.feedburner.com/lifebang" "http://www.ftchinese.com/sc/rss2_full.jsp" "http://www.aigaogao.com/blog/rss.aspx" "http://feeds.feedburner.com/BloggerBuzz" "http://googleajaxsearchapi.blogspot.com/atom.xml" "http://analytics.blogspot.com/atom.xml" "http://code.google.com/feeds/updates.xml" "http://googlemalwareblog.blogspot.com/atom.xml" "http://googlemapsapi.blogspot.com/atom.xml" "http://googleonlinesecurity.blogspot.com/atom.xml" "http://googlewebmastercentral.blogspot.com/atom.xml" "http://adsense.blogspot.com/atom.xml" "http://adwords.blogspot.com/atom.xml" "http://googledesktop.blogspot.com/atom.xml" "http://gmailblog.blogspot.com/atom.xml" "http://googleblog.blogspot.com/atom.xml" "http://googlereader.blogspot.com/atom.xml" "http://www.43folders.com/feed/" "http://blog.del.icio.us/blog/index.rdf" "http://blog.dreamhost.com/feed/" "http://www.dreamhoststatus.com/feed/" "http://feeds.feedburner.com/BurnThisRSS2" "http://blog.outer-court.com/rss.xml" "http://feeds.feedburner.com/googleoperatingsystem" "http://www.joelonsoftware.com/rss.xml" "http://feeds.feedburner.com/mashable" "http://www.mattcutts.com/blog/feed/" "http://radar.oreilly.com/feed" "http://www.readwriteweb.com/rss.xml" "http://www.searchengineblog.com/atom.xml" "http://feeds.feedburner.com/Techcrunch" "http://www.ysearchblog.com/index.xml" "http://www.gearthblog.com/index.xml" "http://google-latlong.blogspot.com/atom.xml" "http://googlemapsmania.blogspot.com/atom.xml" "http://googlesightseeing.com/feed/" "http://feeds.ogleearth.com/ogleearth" "http://www.panoramio.com/blog/feed/" "http://feeds.feedburner.com/psblog" "http://www.bloggingpro.com/feed/" "http://feeds.copyblogger.com/Copyblogger" "http://feeds.feedburner.com/DailyBlogTips" "http://www.doshdosh.com/feed/" "http://feeds.feedburner.com/performancing" "http://feeds.feedburner.com/JohnChowDotCom" "http://www.micropersuasion.com/rss.xml" "http://feeds.feedburner.com/QuickOnlineTips" "http://www.successful-blog.com/feed/"))
 '(org-agenda-files
   '("~/resource/dailyNotes/Note/Tools/Emacs/Emacs-note.org" "/home/stone/resource/dailyNotes/dailyRoutine/Star/resources.org" "/home/stone/resource/dailyNotes/todolist.org"))
 '(org-agenda-insert-diary-extract-time nil)
 '(package-selected-packages
   '(backup-each-save baidu-translate company eaf-markmap elfeed
		      embark-consult epc flycheck fzf indent-guide
		      keycast keyfreq lsp-python-ms lsp-treemacs
		      lsp-ui marginalia mood-one-theme
		      multiple-cursors orderless org-bullets
		      org-download org-roam-ui ox-hugo pandoc-mode
		      rainbow-delimiters rg rust-mode smartparens
		      swiper treemacs-icons-dired
		      treemacs-persp treemacs-projectile treesit-auto
		      vertico web-mode wgrep which-key
		      window-numbering yasnippet-snippets
		      youdao-dictionary))
 '(treemacs-show-hidden-files t))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
