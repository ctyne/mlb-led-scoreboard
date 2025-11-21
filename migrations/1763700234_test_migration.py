from migrations.migration import ConfigMigration


class test_migration(ConfigMigration):
    def up(self):
        self.add_key("test", 1, "config.example.json")

    def down(self):
        self.remove_key("test", "config.example.json")
