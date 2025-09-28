import pygame
import sys
import asyncio
import os # ファイルパスチェック用に追加

# 日本語フォントの設定（ローカル環境からの相対パスを推奨）
FONT_FILE = "NotoSansJP-VariableFont_wght.ttf" 

# ゲームループ全体を非同期関数で定義
async def main():
    # Pygameの初期化
    pygame.init()

    # フォントのパスを決定
    font_path_to_use = FONT_FILE
    if not os.path.exists(FONT_FILE):
        print(f"警告: フォントファイル '{FONT_FILE}' が見つかりません。デフォルトフォントを使用します。")
        font_path_to_use = None

    # ゲームの設定 (定数)
    SCREEN_WIDTH, SCREEN_HEIGHT = 480, 540
    BLOCK_ROWS, BLOCK_COLS = 4, 9
    BLOCK_WIDTH, BLOCK_HEIGHT = 40, 40
    BALL_RADIUS = 10
    PADDLE_WIDTH, PADDLE_HEIGHT = 65, 10

    # 色の設定
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLACK = (0, 0, 0)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ブロック崩し")

    # 表示する文字を指定
    specified_letters = list("食べられる豆は何？らおせち料理としてうに」という願いか「体調を崩さないよ")
    if len(specified_letters) < BLOCK_ROWS * BLOCK_COLS:
        raise ValueError("指定した文字数がブロック数に足りません")

    # ブロックの生成
    blocks = []
    block_letters = {}
    letter_index = 0
    for row in range(BLOCK_ROWS):
        for col in range(BLOCK_COLS):
            block_rect = pygame.Rect(
                col * (BLOCK_WIDTH + 5) + 35,
                SCREEN_HEIGHT - (row + 1) * (BLOCK_HEIGHT + 5) - 35,
                BLOCK_WIDTH,
                BLOCK_HEIGHT
            )
            blocks.append(block_rect)
            block_letters[(block_rect.x, block_rect.y)] = specified_letters[letter_index]
            letter_index += 1

    destroyed_blocks = []

    # パドルとボールの設定
    paddle = pygame.Rect(
        (SCREEN_WIDTH - PADDLE_WIDTH) // 2,
        SCREEN_HEIGHT - (BLOCK_ROWS + 1) * (BLOCK_HEIGHT + 5) - 240,
        PADDLE_WIDTH,
        PADDLE_HEIGHT
    )
    ball = pygame.Rect(
        SCREEN_WIDTH // 2,
        paddle.top - BALL_RADIUS * 2 + 200,
        BALL_RADIUS * 2,
        BALL_RADIUS * 2
    )
    ball_dx, ball_dy = 3, 3
    ball_speed_multiplier = 1.025

    # フォントオブジェクトをここで準備（再描画ごとに作るのは非効率）
    font_block = pygame.font.Font(font_path_to_use, 30)
    font_msg = pygame.font.Font(font_path_to_use, 50) 
    
    clock = pygame.time.Clock()
    game_over = False
    game_started = False
    running = True 

    # メインゲームループ
    while running:
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False 
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_started and not game_over:
                    game_started = True

        # 入力処理
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and paddle.left > 0:
            paddle.move_ip(-5, 0)
        if keys[pygame.K_RIGHT] and paddle.right < SCREEN_WIDTH:
            paddle.move_ip(5, 0)

        # ゲームロジック
        if game_started and not game_over:
            
            # ボールを次の位置に移動
            new_ball_rect = ball.move(ball_dx, ball_dy) 
            
            # --- 壁との反射 ---
            if new_ball_rect.left <= 0 or new_ball_rect.right >= SCREEN_WIDTH:
                ball_dx *= -1
            
            # 上端に当たったらゲームオーバー (元の仕様)
            if new_ball_rect.top <= 0:
                game_over = True
            
            # 下端に当たったら跳ね返る (元のコードの仕様)
            if new_ball_rect.bottom >= SCREEN_HEIGHT:
                ball_dy *= -1
                new_ball_rect.bottom = SCREEN_HEIGHT

            # --- パドルとの反射（正確な衝突処理）---
            if new_ball_rect.colliderect(paddle):
                # 衝突があった場合、進行方向に応じて反射
                
                # 1. パドル上部との衝突 (最も一般的)
                if ball.bottom <= paddle.top and ball_dy > 0:
                    ball_dy *= -1
                    new_ball_rect.bottom = paddle.top # 食い込み防止
                
                # 2. パドル下部との衝突 (ボールがパドルを通り抜けそうになった場合)
                elif ball.top >= paddle.bottom and ball_dy < 0:
                    ball_dy *= -1
                    new_ball_rect.top = paddle.bottom # 食い込み防止
                    
                # 3. 側面との衝突
                else:
                    ball_dx *= -1
                
                # 速度上昇
                ball_dx *= ball_speed_multiplier
                ball_dy *= ball_speed_multiplier

            # --- ブロックとの衝突処理 ---
            hit_index = new_ball_rect.collidelist(blocks)
            if hit_index != -1:
                hit_block = blocks.pop(hit_index)
                destroyed_blocks.append((hit_block.center, block_letters[(hit_block.x, hit_block.y)]))
                del block_letters[(hit_block.x, hit_block.y)]

                # 衝突面の判定
                # ボールの移動方向を考慮し、最も浅くめり込んだ方向の速度を反転させるのが理想ですが、
                # 元のコードのロジックを維持しつつ、速度を反転させます。
                
                # 衝突前のボールの位置とブロックの位置を比較して反射方向を決定
                if ball.center[1] < hit_block.top or ball.center[1] > hit_block.bottom:
                    # 上下方向から衝突
                    ball_dy *= -1
                else:
                    # 左右方向から衝突
                    ball_dx *= -1

                # 速度上昇
                ball_dx *= ball_speed_multiplier
                ball_dy *= ball_speed_multiplier
            
            # 最終的なボールの位置を更新
            ball = new_ball_rect
            
        # 描画処理
        screen.fill(WHITE)
        for block in blocks:
            pygame.draw.rect(screen, BLUE, block)
        pygame.draw.rect(screen, GREEN, paddle)
        pygame.draw.ellipse(screen, RED, ball)

        # 壊れたブロックの文字を描画
        for pos, letter in destroyed_blocks:
            text = font_block.render(letter, True, BLACK)
            screen.blit(text, (pos[0] - text.get_width() // 2, pos[1] - text.get_height() // 2))

        # ゲームオーバーまたはスタートメッセージの表示
        if game_over:
            text = font_msg.render("ゲームオーバー", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))
        elif not game_started:
            text = font_msg.render("スペースキーでスタート", True, BLACK)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

        # 画面更新
        pygame.display.flip()
        
        # ★ 動作をスムーズにするための非同期待機（pygbagで必須）
        await asyncio.sleep(0) 

        # フレームレート制御
        clock.tick(60)

    # ループ終了後の処理
    pygame.quit()


# スクリプトのエントリーポイント
if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(main())