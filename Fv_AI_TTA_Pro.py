import requests
import json
import os
import time
from datetime import datetime
import re

# 配置文件路径
CONFIG_FILE = "FV_tts_config.json"

# API基础URL
API_BASE_URL = "https://ttsapi.fineshare.com/v1"

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "voices": {
        "default": {
            "voice": "12c9881d-54cc-4e5d-93b6-eb30aed94d9d-54660",
            "amotion": "friendly",
            "format": "mp3"
        }
    },
    "output_paths": {
        "default": "/storage/emulated/0/Download/output"
    },
    # 中英文情感映射
    "emotion_mapping": {
        "cheerful": "开心",
        "sad": "悲伤",
        "chat": "聊天",
        "whispering": "耳语",
        "newscast": "新闻播报",
        "empathetic": "共情",
        "relieved": "放松",
        "assistant": "助手",
        "customerservice": "客服",
        "angry": "生气",
        "excited": "兴奋",
        "friendly": "友好",
        "terrified": "恐惧",
        "shouting": "喊叫",
        "unfriendly": "不友好",
        "hopeful": "希望",
        "narration-professional": "专业旁白",
        "newscast-casual": "休闲新闻",
        "newscast-formal": "正式新闻",
        "conversation": "对话",
        "calm": "平静",
        "affectionate": "深情",
        "disgruntled": "不满",
        "fearful": "害怕",
        "gentle": "温柔",
        "lyrical": "抒情",
        "serious": "严肃",
        "poetry-reading": "诗歌朗诵",
        "chat-casual": "休闲聊天",
        "sorry": "抱歉",
        "narration-relaxed": "轻松旁白",
        "embarrassed": "尴尬",
        "depressed": "沮丧",
        "sports-commentary": "体育解说",
        "sports-commentary-excited": "激动体育解说",
        "documentary-narration": "纪录片旁白",
        "livecommercial": "直播广告",
        "envious": "嫉妒",
        "story": "讲故事",
        "advertisement-upbeat": " upbeat广告"
    },
    "format_options": ["mp3", "wav", "ogg"],
    "history": []
}

class TTSManager:
    def __init__(self):
        self.config = self.load_config()
        self.current_voice = "default"
        self.current_output_path = "default"
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    # 兼容旧版本配置
                    if "output_paths" not in config:
                        config["output_paths"] = DEFAULT_CONFIG["output_paths"].copy()
                    if "emotion_mapping" not in config:
                        config["emotion_mapping"] = DEFAULT_CONFIG["emotion_mapping"].copy()
                    if "format_options" not in config:
                        config["format_options"] = DEFAULT_CONFIG["format_options"].copy()
                    config.setdefault("history", [])
                    return config
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置文件"""
        # 确保输出目录存在
        for path in self.config["output_paths"].values():
            os.makedirs(path, exist_ok=True)
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def get_headers(self):
        """获取API请求头"""
        return {"x-api-key": self.config["api_key"]}
    
    def set_api_key(self, key):
        """设置API密钥"""
        self.config["api_key"] = key
        self.save_config()
        return "🔑 API密钥已保存！"
    
    def list_voices(self):
        """获取可用声音列表"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/voices",
                params={"category": "all", "gender": "all", "language": "all"},
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code != 200:
                return f"❌ 请求失败: 状态码 {response.status_code}, 响应: {response.text[:100]}"
            
            data = response.json()
            # 兼容不同响应结构
            voices = data.get("voices") or data.get("data", {}).get("voices") or []
            return voices
        except Exception as e:
            return f"❌ 网络错误: {str(e)}"
    
    def create_voice_profile(self, name, voice, amotion=None, format="mp3"):
        """创建自定义声音配置"""
        # 检查名称是否已存在
        if name in self.config["voices"]:
            return "⚠️ 配置名称已存在！"
        
        self.config["voices"][name] = {
            "voice": voice,
            "amotion": amotion,
            "format": format
        }
        self.save_config()
        return f"🎶 声音配置 '{name}' 已创建！"
    
    def edit_voice_profile(self, name, voice=None, amotion=None, format=None):
        """编辑现有声音配置"""
        if name not in self.config["voices"]:
            return "⚠️ 配置不存在"
        
        profile = self.config["voices"][name]
        if voice: profile["voice"] = voice
        if amotion: profile["amotion"] = amotion
        if format: profile["format"] = format
        
        self.save_config()
        return f"🎛️ 声音配置 '{name}' 已更新！"
    
    def delete_voice_profile(self, name):
        """删除声音配置"""
        if name == "default":
            return "❌ 不能删除默认配置"
            
        if name in self.config["voices"]:
            del self.config["voices"][name]
            # 如果删除的是当前配置，重置为默认
            if self.current_voice == name:
                self.current_voice = "default"
            self.save_config()
            return f"🗑️ 声音配置 '{name}' 已删除！"
        return "⚠️ 配置不存在"
    
    def rename_voice_profile(self, old_name, new_name):
        """重命名声音配置"""
        if old_name not in self.config["voices"]:
            return "⚠️ 原配置不存在"
        if new_name in self.config["voices"]:
            return "⚠️ 新名称已存在"
        
        # 更新配置
        self.config["voices"][new_name] = self.config["voices"][old_name]
        del self.config["voices"][old_name]
        
        # 更新当前选择
        if self.current_voice == old_name:
            self.current_voice = new_name
        
        self.save_config()
        return f"🔄 配置已从 '{old_name}' 重命名为 '{new_name}'"
    
    def add_output_path(self, name, path):
        """添加输出路径配置"""
        if name in self.config["output_paths"]:
            return "⚠️ 路径名称已存在"
        
        # 创建目录
        os.makedirs(path, exist_ok=True)
        self.config["output_paths"][name] = path
        self.save_config()
        return f"📁 输出路径 '{name}' 已添加"
    
    def clear_history(self):
        """清空历史记录"""
        self.config["history"] = []
        self.save_config()
        return "✅ 历史记录已清空！"
    
    def test_api_connection(self):
        """测试API连接状态"""
        print("\n测试API连接...")
        try:
            # 将HEAD方法改为GET方法
            response = requests.get(
                f"{API_BASE_URL}/voices",
                headers=self.get_headers(),
                timeout=5
            )
            if response.status_code == 200:
                return True
            else:
                print(f"❌ API响应异常 (状态码 {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ 无法连接到API: {str(e)}")
            return False
    
    def select_emotion(self, current_value=None):
        """显示中文情感选择菜单并获取用户选择"""
        print("\n\033[1;36m情感类型 (可选):\033[0m")
        cn_emotions = list(self.config["emotion_mapping"].values())
        if current_value:
            # 查找当前值的英文对应中文
            current_cn = next(
                (cn for en, cn in self.config["emotion_mapping"].items() if en == current_value), 
                "无"
            )
        else:
            current_cn = "无"
        
        for i, cn_emotion in enumerate(cn_emotions, 1):
            indicator = " (当前)" if cn_emotion == current_cn else ""
            print(f"{i}. {cn_emotion}{indicator}")
        
        choice = input("\n请选择序号(回车表示不设置情感): ")
        if choice.strip() == "":
            return None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(cn_emotions):
                # 将中文选项映射回英文
                cn_selected = cn_emotions[index]
                en_selected = next(
                    en for en, cn in self.config["emotion_mapping"].items() 
                    if cn == cn_selected
                )
                return en_selected
        except:
            pass
        
        return current_value if current_value else None

    def select_from_menu(self, title, options, current_value=None):
        """显示选择菜单并获取用户选择"""
        print(f"\n\033[1;36m{title}:\033[0m")
        for i, option in enumerate(options, 1):
            indicator = " (当前)" if current_value == option else ""
            print(f"{i}. {option}{indicator}")
        
        choice = input("\n请选择: ")
        if choice.strip() == "":
            return current_value
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index]
        except:
            pass
        return current_value if current_value else options[0]

    def format_filename(self, text, format_ext):
        """根据文本生成文件名（取前20个字符+时间戳）"""
        # 提取前20个字符作为文件名
        clean_text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', '_', text[:20])
        if not clean_text:
            clean_text = "tts_audio"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{clean_text}_{timestamp}.{format_ext}"

    def text_to_speech(self, text, voice_profile_name=None):
        """文字转语音"""
        # 如果没有指定声音配置，使用当前配置
        if voice_profile_name is None:
            voice_profile = self.config["voices"].get(self.current_voice, {})
            profile_name = self.current_voice  # 用于历史记录
        else:
            voice_profile = self.config["voices"].get(voice_profile_name, {})
            profile_name = voice_profile_name  # 用于历史记录
        
        if not voice_profile:
            return "❌ 未找到声音配置"
        
        try:
            payload = {
                "voice": voice_profile["voice"],
                "amotion": voice_profile.get("amotion"),
                "format": voice_profile.get("format", "mp3"),
                "speech": text
            }
            
            response = requests.post(
                f"{API_BASE_URL}/text-to-speech",
                json=payload,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                download_url = data.get("downloadUrl")
                format_ext = voice_profile.get("format", "mp3")
                
                # 获取输出路径
                output_dir = self.config["output_paths"].get(self.current_output_path, "./")
                
                # 使用新的文件名生成方式
                filename = os.path.join(output_dir, self.format_filename(text, format_ext))
                
                # 下载音频文件
                audio_response = requests.get(download_url)
                with open(filename, "wb") as f:
                    f.write(audio_response.content)
                
                # 保存历史记录 - 使用配置名称而不是声音ID
                self.config["history"].append({
                    "text": text,
                    "profile_name": profile_name,  # 配置名称
                    "amotion": voice_profile.get("amotion"),
                    "timestamp": datetime.now().isoformat(),
                    "filename": filename
                })
                self.save_config()
                
                return f"🔊 语音生成成功！保存为: {filename}"
            else:
                return f"❌ 请求失败: {response.json().get('error', {}).get('message', '未知错误')}"
        except Exception as e:
            return f"❌ 发生错误: {str(e)}"

def print_menu():
    """打印菜单 - 根据图片样式优化"""
    menu_width = 40
    separator = "=" * menu_width
    
    print(f"\n\033[1;36m{separator}\033[0m")
    print("\033[1;35m AI真人语音生成高级版 \033[0m".center(menu_width))
    print(f"\033[1;36m{separator}\033[0m")
    
    menu_items = [
        "1. 真人语音生成🎧 ",
        "2. 管理声音配置⚙️ ",
        "3. 设置API密钥🔑 ",
        "4. 查看历史记录📜 ",
        "5. 管理输出路径📁 ",
        "6. 测试API连接📶 ",
        "7. 退出🚪 "
    ]
    
    for item in menu_items:
        print(f"\033[1;37m{item}\033[0m")
    
    print(f"\033[1;36m{separator}\033[0m")

def manage_voice_profiles(manager):
    """管理声音配置界面"""
    while True:
        menu_width = 40
        separator = "=" * menu_width
        
        print(f"\n\033[1;33m{separator}\033[0m")
        print("\033[1;33m 声音配置管理 \033[0m".center(menu_width))
        print(f"\033[1;33m{separator}\033[0m")
        
        menu_items = [
            "1. 列出所有配置",
            "2. 创建新配置",
            "3. 编辑配置",
            "4. 删除配置",
            "5. 切换当前配置",
            "6. 返回主菜单"
        ]
        
        for item in menu_items:
            print(f"\033[1;37m{item}\033[0m")
        
        print(f"\033[1;33m{separator}\033[0m")
        
        choice = input("\n请选择操作: ")
        
        if choice == "1":
            print("\n当前声音配置:")
            for name, profile in manager.config["voices"].items():
                is_current = " (当前使用)" if manager.current_voice == name else ""
                # 将英文情感转换为中文
                emotion = manager.config["emotion_mapping"].get(
                    profile.get("amotion", "无"), 
                    "无"
                )
                print(f"- {name}{is_current}: {profile['voice']}, 情感: {emotion}")
        
        elif choice == "2":
            name = input("\n输入新配置名称: ")
            if name in manager.config["voices"]:
                print("⚠️ 配置名称已存在！")
                continue
                
            voice_id = input("输入声音ID（如 'ios-5110'）: ").strip()
            if not voice_id:
                print("❌ 声音ID不能为空")
                continue
                
            # 使用新的中文情感选择
            amotion = manager.select_emotion()
            
            fmt = manager.select_from_menu(
                "音频格式",
                manager.config["format_options"],
                "mp3"
            )
            
            print(manager.create_voice_profile(name, voice_id, amotion, fmt))
        
        elif choice == "3":
            print("\n可用配置:")
            voices = list(manager.config["voices"].keys())
            for i, name in enumerate(voices, 1):
                is_current = " (当前)" if manager.current_voice == name else ""
                print(f"{i}. {name}{is_current}")
            choice_idx = int(input("\n选择要编辑的配置编号: ")) - 1
            name = voices[choice_idx]
            profile = manager.config["voices"][name]
            
            print(f"\n编辑配置: {name}")
            print(f"当前声音: {profile['voice']}")
            
            # 将英文情感转换为中文
            emotion = manager.config["emotion_mapping"].get(
                profile.get("amotion", "无"), 
                "无"
            )
            print(f"当前情感: {emotion}")
            print(f"当前格式: {profile.get('format', 'mp3')}")
            
            new_voice = input(f"新声音ID（回车保持当前）: ") or profile['voice']
            
            # 使用新的中文情感选择
            print("\n请选择新情感:")
            new_amotion = manager.select_emotion(profile.get('amotion'))
            
            new_format = input(f"新格式（回车保持当前）: ") or profile.get('format', 'mp3')
            
            print(manager.edit_voice_profile(name, new_voice, new_amotion, new_format))
        
        elif choice == "4":
            print("\n可用配置:")
            voices = list(manager.config["voices"].keys())
            for i, name in enumerate(voices, 1):
                print(f"{i}. {name}")
            choice_idx = int(input("\n选择要删除的配置编号: ")) - 1
            name = voices[choice_idx]
            
            if name == "default":
                print("❌ 不能删除默认配置！")
                continue
                
            confirm = input(f"确定要删除 '{name}' 配置吗? (y/n): ").lower()
            if confirm == "y":
                print(manager.delete_voice_profile(name))
        
        elif choice == "5":
            print("\n可用配置:")
            voices = list(manager.config["voices"].keys())
            for i, name in enumerate(voices, 1):
                is_current = " (当前)" if manager.current_voice == name else ""
                print(f"{i}. {name}{is_current}")
            choice_idx = int(input("\n选择配置编号: ")) - 1
            manager.current_voice = voices[choice_idx]
            print(f"\n✅ 当前配置已切换为: {manager.current_voice}")
        
        elif choice == "6":
            break
        
        time.sleep(1)

def manage_output_paths(manager):
    """管理输出路径配置"""
    while True:
        menu_width = 40
        separator = "=" * menu_width
        
        print(f"\n\033[1;34m{separator}\033[0m")
        print("\033[1;34m 输出路径管理 \033[0m".center(menu_width))
        print(f"\033[1;34m{separator}\033[0m")
        
        menu_items = [
            "1. 列出所有路径",
            "2. 添加新路径",
            "3. 删除路径",
            "4. 切换当前路径",
            "5. 返回主菜单"
        ]
        
        for item in menu_items:
            print(f"\033[1;37m{item}\033[0m")
        
        print(f"\033[1;34m{separator}\033[0m")
        
        choice = input("\n请选择操作: ")
        
        if choice == "1":
            print("\n当前输出路径:")
            for name, path in manager.config["output_paths"].items():
                is_current = " (当前使用)" if manager.current_output_path == name else ""
                print(f"- {name}{is_current}: {path}")
        
        elif choice == "2":
            name = input("\n输入路径名称: ")
            path = input("输入完整路径: ").strip()
            
            if not os.path.exists(path):
                create = input("目录不存在，是否创建? (y/n): ").lower()
                if create != "y":
                    continue
                os.makedirs(path, exist_ok=True)
            
            print(manager.add_output_path(name, path))
        
        elif choice == "3":
            paths = list(manager.config["output_paths"].keys())
            if len(paths) <= 1:
                print("❌ 至少需要保留一个输出路径！")
                continue
                
            print("\n可用路径:")
            for i, name in enumerate(paths, 1):
                print(f"{i}. {name}")
            choice_idx = int(input("\n选择要删除的路径编号: ")) - 1
            name = paths[choice_idx]
            
            if name == "default":
                print("❌ 不能删除默认路径！")
                continue
                
            confirm = input(f"确定要删除 '{name}' 路径吗? (y/n): ").lower()
            if confirm == "y":
                del manager.config["output_paths"][name]
                # 如果删除的是当前路径，切换到默认
                if manager.current_output_path == name:
                    manager.current_output_path = "default"
                print(f"🗑️ 输出路径 '{name}' 已删除！")
                manager.save_config()
        
        elif choice == "4":
            print("\n可用路径:")
            paths = list(manager.config["output_paths"].keys())
            for i, name in enumerate(paths, 1):
                is_current = " (当前)" if manager.current_output_path == name else ""
                print(f"{i}. {name}{is_current}")
            choice_idx = int(input("\n选择路径编号: ")) - 1
            manager.current_output_path = paths[choice_idx]
            print(f"\n✅ 当前输出路径已切换为: {manager.current_output_path}")
        
        elif choice == "5":
            break
        
        time.sleep(1)

def main():
    manager = TTSManager()
    
    # 确保输出目录存在
    for path in manager.config["output_paths"].values():
        os.makedirs(path, exist_ok=True)
    
    while True:
        print_menu()
        choice = input("\n请选择操作: ")
        
        if choice == "1":
            text = input("\n请输入要转换的文本: ")
            
            # 列出所有声音配置
            print("\n\033[1;32m可用声音配置:\033[0m")
            voices = list(manager.config["voices"].keys())
            for i, name in enumerate(voices, 1):
                is_current = " (当前)" if manager.current_voice == name else ""
                print(f"{i}. {name}{is_current}")
            
            # 添加序号选择功能
            input_prompt = "请选择配置序号(回车使用当前): "
            selected_config = None
            
            try:
                choice_input = input(input_prompt)
                if choice_input.strip():  # 如果用户输入了内容
                    choice_idx = int(choice_input) - 1
                    if 0 <= choice_idx < len(voices):
                        selected_config = voices[choice_idx]
                    else:
                        print("❌ 选择无效，将使用当前配置")
                else:
                    print("✅ 使用当前配置")
            except ValueError:
                print("❌ 输入无效，将使用当前配置")
            
            # 列出所有输出路径
            print("\n\033[1;32m可用输出路径:\033[0m")
            paths = list(manager.config["output_paths"].keys())
            for i, name in enumerate(paths, 1):
                is_current = " (当前)" if manager.current_output_path == name else ""
                print(f"{i}. {name}{is_current}")
            
            # 路径选择
            try:
                choice_input = input("请选择输出路径序号(回车使用当前): ")
                if choice_input.strip():  # 如果用户输入了内容
                    choice_idx = int(choice_input) - 1
                    if 0 <= choice_idx < len(paths):
                        manager.current_output_path = paths[choice_idx]
            except ValueError:
                print("❌ 输入无效，将使用当前输出路径")
            
            print("\n生成中...")
            result = manager.text_to_speech(text, selected_config)
            print(f"\n{result}")
        
        elif choice == "2":
            manage_voice_profiles(manager)
        
        elif choice == "3":
            key = input("\n请输入API密钥: ")
            print(manager.set_api_key(key))
        
        elif choice == "4":
            while True:
                print("\n历史记录:")
                if not manager.config["history"]:
                    print("暂无历史记录")
                else:
                    # 只显示最近的5条记录
                    recent_history = manager.config["history"][-5:]
                    for i, record in enumerate(reversed(recent_history), 1):
                        print(f"{i}. {record['timestamp'][:10]} {record['timestamp'][11:19]}")
                        print(f"   配置: {record['profile_name']}")   # 显示配置名称
                        if record.get('amotion'):
                            # 将英文情感转换为中文
                            emotion = manager.config["emotion_mapping"].get(
                                record['amotion'], 
                                record['amotion']
                            )
                            print(f"   情感: {emotion}")
                        print(f"   文件: {record['filename']}")
                        print("-" * 40)
                
                print("\n操作选项:")
                print("1. 清空历史记录")
                print("2. 返回主菜单")
                
                action = input("请选择操作: ")
                
                if action == "1":
                    confirm = input("确定要清空历史记录吗？(y/n): ").lower()
                    if confirm == 'y':
                        print(manager.clear_history())
                    break
                elif action == "2":
                    break
                else:
                    print("❌ 请选择有效的选项")
        
        elif choice == "5":
            manage_output_paths(manager)
        
        elif choice == "6":
            if manager.test_api_connection():
                print("✅ API连接正常")
            else:
                print("❌ 无法连接到API，请检查API密钥和网络连接")
        
        elif choice == "7":
            print("\n感谢使用，再见！")
            break
        
        time.sleep(1)

if __name__ == "__main__":
    main()
