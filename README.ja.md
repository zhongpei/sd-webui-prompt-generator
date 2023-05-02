# sd-webui-prompt-generator

## README 翻訳

-   [英語](README.en.md)
-   [簡体字中国語](README.md)
-   [日本](README.ja.md)
-   [ロシア](README.ru.md)

## 概要

Generator Prompt は、プロンプトの作成を支援するために作成されました。

-   プロンプトを英語に翻訳する
-   小さくて速い Prompt 生成モデル
-   プロンプトの詳細を自動的に生成する
    -   標準モード
    -   二次元（アニメーション）モード
-   プロンプトを自動的にフォーマットする

## 使用法

-   `F`ボタンの書式設定
-   `G`ボタン翻訳 + 生成

![ui.png](./docs/ui.png)

### モデルのダウンロード

から自動的にモデル化[ハグ顔](https://huggingface.co/)ダウンロード、ネットワークが良好でない場合は、手動でダウンロードできます[バイドゥ](https://pan.baidu.com/s/1RRo30reGmhRzFlGrZG74tg?pwd=mh96)

-   オフライン ダウンロード
    -   [バイドゥ](https://pan.baidu.com/s/1RRo30reGmhRzFlGrZG74tg?pwd=mh96)抽出コード：mh96
    -   に抽出`stable-diffusion-webui\models`

-   モデル公式サイト
    -   [アニメ何でもpromptgen-v2](https://huggingface.co/FredZhang7/anime-anything-promptgen-v2)
    -   [distilgpt2](https://huggingface.co/distilgpt2)
    -   [distilgpt2-stable-diffusion-v2](https://huggingface.co/FredZhang7/distilgpt2-stable-diffusion-v2)

## 設定

-   `model type`
    -   `normal`一般的なパターン
    -   `anime`二次元
-   `model device`
    -   `cpu`ビデオメモリを占有せず、やや遅い
    -   `cuda`メモリ使用量、高速
-   `translate `
    -   `none`翻訳しないでください
    -   `google`グーグル翻訳
    -   `youdao`ヨウダオ翻訳
-   `translate from`
    -   `zh`中文
    -   `jp`日文
    -   `ru`ロシア
-   `genertor temperature`生成温度、0.0 ～ 1.0、高いほどランダム

![img.png](./docs/setting.png)
