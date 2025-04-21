import base64
import hashlib
import logging
from urllib.parse import quote, unquote
import secrets
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Secret key for URL encoding/decoding (keep this secure in a production environment)
URL_ENCODING_KEY = os.environ.get("URL_ENCODING_KEY") or "mySecretKey123"

def encode_url(original_url):
    """
    URLを独自のアルゴリズムでエンコードする関数
    
    Args:
        original_url (str): エンコードする元のURL
        
    Returns:
        str: エンコードされたURL文字列
    """
    try:
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
        
        logger.debug(f"元のURL: {original_url}")
        logger.debug(f"エンコード結果: {result}")
        return result
    except Exception as e:
        logger.exception(f"エラー: URLのエンコード中にエラーが発生しました: {str(e)}")
        return None

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
            logger.error(f"エラー: 無効なエンコードID（短すぎます）: {encoded_id}")
            return None
            
        # ハッシュ部分とエンコード部分を抽出
        hash_part = encoded_id[:8]
        encoded_part = encoded_id[8:]
        
        # ハッシュを検証
        calculated_hash = hashlib.sha256((encoded_part + URL_ENCODING_KEY).encode()).hexdigest()[:8]
        if calculated_hash != hash_part:
            logger.error(f"エラー: ハッシュ検証に失敗しました: {encoded_id}")
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
        
        logger.debug(f"エンコードされたID: {encoded_id}")
        logger.debug(f"デコード結果: {original_url}")
        return original_url
        
    except Exception as e:
        logger.exception(f"エラー: URLのデコード中にエラーが発生しました: {str(e)}")
        return None