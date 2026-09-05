import random
from dataclasses import dataclass
from typing import Optional

@dataclass
class CombatEntity:
    name: str
    hp: int
    max_hp: int
    damage: float
    armor: float
    is_player: bool

class CombatEngine:
    def __init__(self, player: CombatEntity, enemy: CombatEntity):
        self.player = player
        self.enemy = enemy
        self.turn = 1
        self.log: list[str] = []
        self.is_finished = False
        self.winner: Optional[CombatEntity] = None

    def execute_attack(self, attacker: CombatEntity, defender: CombatEntity) -> int:
        """Kalkulacja obrażeń bazowa z elementem losowości i redukcją przez pancerz."""
        base_dmg = attacker.damage
        # +/- 15% losowości
        variance = random.uniform(0.85, 1.15)
        raw_dmg = base_dmg * variance
        
        # Redukcja: Armor redukuje płasko lub procentowo, tu dla uproszczenia procentowo
        # np. armor 10 redukuje 10%
        damage_reduction = min(defender.armor / 100.0, 0.75) # max 75% redukcji
        
        final_dmg = max(int(raw_dmg * (1.0 - damage_reduction)), 1)
        defender.hp -= final_dmg
        
        return final_dmg

    def process_player_action(self, action: str) -> None:
        if self.is_finished:
            return

        # Player turn
        if action == "attack":
            dmg = self.execute_attack(self.player, self.enemy)
            self.log.append(f"⚔️ **{self.player.name}** atakuje za **{dmg}** obrażeń!")
        elif action == "potion":
            heal = int(self.player.max_hp * 0.3)
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.log.append(f"🧪 **{self.player.name}** leczy się za **{heal}** HP!")
        elif action == "flee":
            self.is_finished = True
            self.log.append(f"🏃 **{self.player.name}** ucieka z pola walki!")
            return

        if self.enemy.hp <= 0:
            self.is_finished = True
            self.winner = self.player
            self.log.append(f"🎉 **{self.enemy.name}** został pokonany!")
            return

        # Enemy turn
        self.process_enemy_turn()
        
    def process_enemy_turn(self):
        dmg = self.execute_attack(self.enemy, self.player)
        self.log.append(f"💀 **{self.enemy.name}** kontratakuje za **{dmg}** obrażeń!")
        
        if self.player.hp <= 0:
            self.is_finished = True
            self.winner = self.enemy
            self.log.append(f"☠️ **{self.player.name}** zginął w walcie...")
            
        self.turn += 1

    def get_status_embed(self, discord_embed_class) -> object:
        """Pomocnicza metoda generująca embed podglądu."""
        embed = discord_embed_class(
            title=f"Walka: {self.player.name} vs {self.enemy.name} (Tura {self.turn})",
            color=0xff0000 if self.is_finished and self.winner == self.enemy else 0x00ff00
        )
        
        embed.add_field(
            name=self.player.name, 
            value=f"HP: {max(0, self.player.hp)}/{self.player.max_hp}", 
            inline=True
        )
        embed.add_field(
            name=self.enemy.name, 
            value=f"HP: {max(0, self.enemy.hp)}/{self.enemy.max_hp}", 
            inline=True
        )
        
        log_text = "\n".join(self.log[-5:]) if self.log else "Walka się rozpoczyna!"
        embed.add_field(name="Dziennik walki", value=log_text, inline=False)
        
        return embed
