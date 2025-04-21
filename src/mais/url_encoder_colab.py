"""
URLエンコーダー - 独自の暗号化アルゴリズムを使用してURLをエンコード/デコードするサンプルコード
Google Colabで実行するためのコード例

実行方法:
1. Google Colabを開く: https://colab.research.google.com/
2. このコードをコピーして新しいノートブックに貼り付ける
3. 各セルを実行して結果を確認する
"""

import base64
import hashlib
from urllib.parse import quote, unquote

# 秘密鍵 (実際の運用ではより安全な方法で管理すべきです)
URL_ENCODING_KEY = "mySecretKey123"

def encode_url(original_url):
    """
    URLを独自のアルゴリズムでエンコードする関数
    
    Args:
        original_url (str): エンコードする元のURL
        
    Returns:
        str: エンコードされたURL文字列
    """
    # 特殊文字を処理するためにURLをクォートする
    safe_url = quote(original_url)
    
    # base64でエンコード
    encoded = base64.urlsafe_b64encode(safe_url.encode()).decode()
    
    # パディング文字(=)を削除（URLセーフにするため）
    encoded = encoded.rstrip("=")
    
    # 検証用のハッシュを追加（SHA-256ハッシュの最初の8文字）
    hash_signature = hashlib.sha256((encoded + URL_ENCODING_KEY).encode()).hexdigest()[:8]
    
    # ハッシュとエンコードされた文字列を結合
    result = f"{hash_signature}{encoded}"
    
    print(f"元のURL: {original_url}")
    print(f"エンコード結果: {result}")
    return result

def decode_url(encoded_id):
    """
    エンコードされたURLを元のURLにデコードする関数
    
    Args:
        encoded_id (str): エンコードされたURL識別子
        
    Returns:
        str: デコードされた元のURL（デコードに失敗した場合はNone）
    """
    try:
        if len(encoded_id) < 8:
            print(f"エラー: 無効なエンコードID（短すぎます）: {encoded_id}")
            return None
            
        # ハッシュ部分とエンコード部分を抽出
        hash_part = encoded_id[:8]
        encoded_part = encoded_id[8:]
        
        # ハッシュを検証
        calculated_hash = hashlib.sha256((encoded_part + URL_ENCODING_KEY).encode()).hexdigest()[:8]
        if calculated_hash != hash_part:
            print(f"エラー: ハッシュ検証に失敗しました: {encoded_id}")
            return None
        
        # 必要に応じてパディングを追加
        padding_needed = len(encoded_part) % 4
        if padding_needed:
            encoded_part += "=" * (4 - padding_needed)
        
        # base64をデコード
        decoded_bytes = base64.urlsafe_b64decode(encoded_part)
        safe_url = decoded_bytes.decode()
        
        # URLアンクォートして元のURLを取得
        original_url = unquote(safe_url)
        
        print(f"エンコードされたID: {encoded_id}")
        print(f"デコード結果: {original_url}")
        return original_url
        
    except Exception as e:
        print(f"エラー: URLのデコード中にエラーが発生しました: {str(e)}")
        return None

# === 使用例 ===

# 例1: URLをエンコード
def example_encode():
    print("\n=== URLエンコードの例 ===")
    urls = [
        "https://www.google.com",
        "https://example.com/path?query=value&param=123",
        "https://日本語.com/こんにちは?検索=世界"
    ]
    
    encoded_results = []
    for url in urls:
        encoded = encode_url(url)
        encoded_results.append(encoded)
        print("-" * 50)
    
    return encoded_results

# 例2: エンコードされたURLをデコード
def example_decode(encoded_ids):
    print("\n=== URLデコードの例 ===")
    for encoded_id in encoded_ids:
        decoded = decode_url(encoded_id)
        print("-" * 50)
    
    # 不正なIDをデコードしようとする例
    print("\n=== 不正なIDのデコード例 ===")
    invalid_ids = [
        "invalid",  # 短すぎる
        "00000000aaaaaaaaaaaa",  # ハッシュが不正
        encoded_ids[0] + "corrupted"  # データ破損
    ]
    
    for invalid_id in invalid_ids:
        decoded = decode_url(invalid_id)
        print("-" * 50)

# すべての例を実行する関数
def run_all_examples():
    # エンコードの例を実行
    encoded_ids = example_encode()
    
    # デコードの例を実行
    example_decode(encoded_ids)
    
    print("\n=== 独自のURLでテスト ===")
    print("以下に自分でテストしたいURLを入力してください:")
    print("例: encode('https://example.com')")
    print("例: decode('46674d94aHR0cHMlM0EvL2V4YW1wbGUuY29t')")

# この行をコメント解除すると自動的に例が実行されます
# run_all_examples()

# === Colabでの対話的な使用 ===
# Colabで以下のように関数を呼び出せます:
# 
# encode_url("https://example.com")
# decode_url("46674d94aHR0cHMlM0EvL2V4YW1wbGUuY29t")