from PIL import Image
import os

class ICOGenerator:
    RESOLUTIONS = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    
    @staticmethod
    def create_ico(image, selected_sizes, output_path):
        """
        선택된 해상도로 ICO 파일 생성
        """
        try:
            # Pillow의 ICO 저장 기능 사용 (간단)
            sizes = [(size, size) for size in selected_sizes if size <= image.size[0]]
            image.save(output_path, format='ICO', sizes=sizes, append_images=[])
            return True, f"ICO 생성 완료: {len(sizes)}개 해상도"
        except Exception as e:
            return False, f"ICO 생성 실패: {str(e)}"
    
    @staticmethod
    def validate_resolutions(image_size, selected_sizes):
        """유효한 해상도만 필터링"""
        max_size = min(image_size)
        return [s for s in selected_sizes if s <= max_size]